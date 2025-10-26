#!/usr/bin/env python3
"""
Script para probar el flujo completo de generación de pruebas de carga.
Ejecuta una prueba de carga contra demo-test-api y verifica que los datos
generados sigan el schema del OAS.
"""
import requests
import json
import time

BACKEND_URL = "http://localhost:8000"
DEMO_API_URL = "http://localhost:8020"

def test_backend_health():
    """Verificar que el backend esté funcionando."""
    print("1. Verificando health del backend...")
    response = requests.get(f"{BACKEND_URL}/health")
    print(f"   ✓ Backend health: {response.status_code}")
    return response.status_code == 200

def test_demo_api_health():
    """Verificar que demo-test-api esté funcionando."""
    print("2. Verificando health de demo-test-api...")
    response = requests.get(f"{DEMO_API_URL}/health")
    print(f"   ✓ Demo API health: {response.status_code}")
    return response.status_code == 200

def get_openapi_spec():
    """Obtener el OAS de demo-test-api."""
    print("3. Obteniendo OAS de demo-test-api...")
    response = requests.get(f"{DEMO_API_URL}/openapi.json")
    oas = response.json()
    print(f"   ✓ OAS obtenido: {oas['info']['title']}")
    print(f"   ✓ Servidor: {oas['servers'][0]['url']}")

    # Verificar schema de AlumnoCreate
    alumno_schema = oas['components']['schemas']['AlumnoCreate']
    print(f"   ✓ Campos de AlumnoCreate: {list(alumno_schema['properties'].keys())}")
    return json.dumps(oas)

def create_load_test(oas_spec):
    """Crear un test de carga."""
    print("4. Creando test de carga...")

    payload = {
        "api_spec": oas_spec,
        "selected_endpoints": [
            {
                "path": "/alumnos",
                "method": "POST",
                "expected_volumetry": 100,
                "expected_concurrent_users": 10,
                "timeout_ms": 30000
            }
        ]
    }

    response = requests.post(
        f"{BACKEND_URL}/api/v1/load-test/execute",
        json=payload,
        headers={"Content-Type": "application/json"}
    )

    if response.status_code != 202:
        print(f"   ✗ Error creando test: {response.status_code}")
        print(f"   Response: {response.text}")
        return None

    result = response.json()
    job_id = result.get("job_id")
    print(f"   ✓ Test creado con job_id: {job_id}")
    return job_id

def monitor_job(job_id, max_wait=300):
    """Monitorear el progreso del job."""
    print(f"5. Monitoreando job {job_id}...")
    start_time = time.time()

    while True:
        if time.time() - start_time > max_wait:
            print(f"   ✗ Timeout esperando el job")
            return None

        response = requests.get(f"{BACKEND_URL}/api/v1/status/{job_id}")
        if response.status_code != 200:
            print(f"   ✗ Error obteniendo status: {response.status_code}")
            return None

        status = response.json()
        progress = status.get("progress_percentage", 0)
        current_status = status.get("status", "unknown")
        message = status.get("status_message", "")

        print(f"   → {current_status}: {progress:.1f}% - {message}")

        if current_status == "FINISHED":
            print(f"   ✓ Job completado!")
            return status
        elif current_status == "FAILED":
            error = status.get("error_message", "Unknown error")
            print(f"   ✗ Job falló: {error}")
            return None

        time.sleep(2)

def verify_generated_script(job_id):
    """Verificar que el script K6 generado tenga datos correctos."""
    print(f"6. Verificando script K6 generado...")

    # Obtener el último script generado
    import subprocess
    result = subprocess.run(
        ["docker", "exec", "loadtester-backend", "ls", "-t", "//app/k6_scripts/"],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        print(f"   ✗ Error listando scripts: {result.stderr}")
        return False

    scripts = result.stdout.strip().split('\n')
    if not scripts:
        print(f"   ✗ No se encontraron scripts generados")
        return False

    latest_script = scripts[0]
    print(f"   → Script más reciente: {latest_script}")

    # Leer el contenido del script
    result = subprocess.run(
        ["docker", "exec", "loadtester-backend", "cat", f"//app/k6_scripts/{latest_script}"],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        print(f"   ✗ Error leyendo script: {result.stderr}")
        return False

    script_content = result.stdout

    # Buscar testData en el script
    if "const testData = [" not in script_content:
        print(f"   ✗ No se encontró testData en el script")
        return False

    # Extraer el primer objeto de testData
    start_idx = script_content.find("const testData = [")
    end_idx = script_content.find("];", start_idx)
    test_data_str = script_content[start_idx:end_idx + 2]

    print(f"\n   Primeros 500 caracteres de testData:")
    print(f"   {test_data_str[:500]}")

    # Verificar campos
    valid_fields = {"nombre", "apellido", "edad", "email", "carrera"}
    invalid_fields = {"id_estudiante", "fecha_nacimiento", "telefono", "direccion", "cursos", "semestre", "promedio"}

    has_valid = any(field in test_data_str for field in valid_fields)
    has_invalid = any(field in test_data_str for field in invalid_fields)

    if has_invalid:
        print(f"\n   ✗ FALLO: Se encontraron campos inventados!")
        for field in invalid_fields:
            if field in test_data_str:
                print(f"      - Campo inventado encontrado: {field}")
        return False

    if has_valid:
        print(f"\n   ✓ ÉXITO: Los datos siguen el schema del OAS!")
        for field in valid_fields:
            if field in test_data_str:
                print(f"      - Campo correcto: {field}")
        return True

    print(f"\n   ⚠ ADVERTENCIA: No se encontraron ni campos válidos ni inválidos")
    return False

def main():
    print("=" * 70)
    print("TEST DE FLUJO COMPLETO - GENERACIÓN DE DATOS MOCK")
    print("=" * 70)
    print()

    # 1. Verificar servicios
    if not test_backend_health():
        print("\n✗ Backend no está funcionando")
        return

    if not test_demo_api_health():
        print("\n✗ Demo API no está funcionando")
        return

    # 2. Obtener OAS
    oas_spec = get_openapi_spec()

    # 3. Crear test
    job_id = create_load_test(oas_spec)
    if not job_id:
        print("\n✗ No se pudo crear el test")
        return

    # 4. Monitorear job
    status = monitor_job(job_id)
    if not status:
        print("\n✗ El job no completó correctamente")
        return

    # 5. Verificar script generado
    if verify_generated_script(job_id):
        print("\n" + "=" * 70)
        print("✓ ✓ ✓ PRUEBA EXITOSA ✓ ✓ ✓")
        print("Los datos mock se generaron correctamente siguiendo el OAS")
        print("=" * 70)
    else:
        print("\n" + "=" * 70)
        print("✗ ✗ ✗ PRUEBA FALLIDA ✗ ✗ ✗")
        print("Los datos mock NO siguieron el schema del OAS")
        print("=" * 70)

if __name__ == "__main__":
    main()
