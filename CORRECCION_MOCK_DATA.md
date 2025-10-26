# Corrección del Sistema de Generación de Datos Mock

## Problema Identificado

Los datos mock generados para pruebas de carga NO seguían el schema del OpenAPI Specification (OAS). En su lugar, se generaban campos inventados como:

```json
{
    "id_estudiante": "string",
    "nombre": "string",
    "apellido": "string",
    "fecha_nacimiento": "2024-02-22",
    "email": "string@example.com",
    "telefono": "string",
    "direccion": "string",
    "carrera": "string",
    "semestre": 0,
    "promedio": 0,
    "materias_aprobadas": 0,
    "activo": true
}
```

Cuando el OAS real es:

```json
{
  "nombre": "string",
  "apellido": "string",
  "edad": 0,
  "email": "string",
  "carrera": "string"
}
```

## Cambios Aplicados

### 1. Archivo: `backend/loadtester/infrastructure/external/mock_data_service.py`

#### Método `generate_mock_data` (líneas 29-87)
- ✅ Validación estricta: El schema NO puede estar vacío
- ✅ Para POST/PUT/PATCH: Valida que exista un body schema
- ✅ Lanza excepciones claras si falta el schema
- ✅ Logging completo del schema recibido

#### Método `_generate_body_from_schema` (líneas 256-298)
- ✅ SOLO genera campos definidos en `schema.properties`
- ✅ NUNCA inventa campos adicionales
- ✅ Genera TODOS los campos (requeridos y opcionales) del schema
- ✅ Valida que existan properties antes de generar
- ✅ Logging detallado de campos generados vs schema

#### Métodos Deshabilitados
- ❌ `_generate_with_ai` → Lanza excepción si se llama
- ❌ `_generate_with_faker` → Lanza excepción si se llama
- ❌ `_generate_basic_fallback_data` → Lanza excepción si se llama

### 2. Archivo: `demo-test-api/main.py`

- ✅ Configurado FastAPI para generar OAS con el servidor correcto:
  ```python
  app = FastAPI(
      title="Demo Test API - Alumnos",
      servers=[
          {"url": "http://host.docker.internal:8020", "description": "Demo API Server"}
      ]
  )
  ```

- ✅ Añadido exception handler para errores de validación con logging detallado

## Acciones Realizadas

1. ✅ Base de datos limpiada (eliminados test_data viejos)
2. 🔄 Backend reconstruyéndose SIN caché (en progreso)
3. ⏳ Pendiente: Reiniciar el servicio backend

## Pasos para Verificar la Corrección

### 1. Verificar que el build termine correctamente

```bash
docker-compose logs -f --tail=50 backend
```

### 2. Reiniciar el servicio backend

```bash
docker-compose restart backend
```

### 3. Ejecutar una nueva prueba de carga

1. Acceder a la interfaz web
2. Introducir el OAS: `http://host.docker.internal:8020/openapi.json`
3. Seleccionar el endpoint `POST /alumnos`
4. Configurar parámetros de carga
5. Ejecutar el test

### 4. Verificar los logs

```bash
# Ver logs del backend
docker-compose logs -f backend | grep -A10 "Schema received:"

# Ver logs del demo-test-api
docker-compose logs -f demo_test_api
```

### 5. Verificar el script K6 generado

```bash
# Ver el último script generado
docker exec loadtester-backend ls -lt //app/k6_scripts/ | head -5

# Ver el contenido del testData
docker exec loadtester-backend cat //app/k6_scripts/script_XX.js | grep -A30 "const testData"
```

## Qué Esperar

### Logs del Backend (Correctos)

```
INFO: Schema received: {
  "requestBody": {
    "content": {
      "application/json": {
        "schema": {
          "type": "object",
          "properties": {
            "nombre": {"type": "string"},
            "apellido": {"type": "string"},
            "edad": {"type": "integer"},
            "email": {"type": "string"},
            "carrera": {"type": "string"}
          },
          "required": ["nombre", "apellido", "edad", "email", "carrera"]
        }
      }
    }
  }
}

INFO: Body schema for POST /alumnos: {
  "type": "object",
  "properties": {
    "nombre": {"type": "string"},
    "apellido": {"type": "string"},
    "edad": {"type": "integer"},
    "email": {"type": "string"},
    "carrera": {"type": "string"}
  }
}

INFO: ✓ Sample generated body (following OAS schema): {
  "nombre": "John",
  "apellido": "Doe",
  "edad": 25,
  "email": "john.doe@example.com",
  "carrera": "Ingeniería"
}
```

### testData en Script K6 (Correcto)

```javascript
const testData = [
    {
        "body": {
            "nombre": "John",
            "apellido": "Doe",
            "edad": 25,
            "email": "john.doe@example.com",
            "carrera": "Ingeniería Informática"
        }
    },
    {
        "body": {
            "nombre": "Jane",
            "apellido": "Smith",
            "edad": 23,
            "email": "jane.smith@example.com",
            "carrera": "Ingeniería de Software"
        }
    }
];
```

### Respuesta del demo-test-api (Correcta)

```
Status: 201 Created
Body: {
  "id": 1,
  "nombre": "John",
  "apellido": "Doe",
  "edad": 25,
  "email": "john.doe@example.com",
  "carrera": "Ingeniería Informática"
}
```

## Si el Problema Persiste

Si después de reiniciar sigues viendo campos inventados:

1. **Verificar que el código se copió**:
   ```bash
   docker exec loadtester-backend grep -n "CRITICAL: This method ONLY generates" //app/loadtester/infrastructure/external/mock_data_service.py
   ```
   Debería mostrar la línea con ese comentario.

2. **Limpiar TODO y reconstruir**:
   ```bash
   docker-compose down
   docker-compose build --no-cache
   docker-compose up -d
   ```

3. **Verificar logs en tiempo real** durante la ejecución de la prueba:
   ```bash
   docker-compose logs -f backend demo_test_api
   ```

## Resumen de la Solución

**ANTES**: El sistema usaba métodos con AI o Faker que generaban campos arbitrarios

**AHORA**: El sistema genera datos **EXCLUSIVAMENTE** a partir del schema del OAS:
- Lee `schema.properties` del OpenAPI
- Genera valores **solo** para esos campos
- Respeta los tipos de datos del schema
- NUNCA inventa campos adicionales
- Falla explícitamente si el schema está vacío o mal formado
