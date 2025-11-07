# Instrucciones para Instalación y Validación Manual

## FASE 1 - Validación de Infraestructura de Testing

### Paso 1: Navegar al directorio backend

```bash
cd "g:/Mi unidad/PSU-IA/Q2/TF1/src/backend"
```

### Paso 2: Verificar que el venv existe y activarlo

```bash
# Verificar que existe
ls ../.venv/Scripts/

# Activar el venv (en Git Bash o WSL)
source ../.venv/Scripts/activate

# O en CMD de Windows
..\.venv\Scripts\activate.bat

# O en PowerShell
..\.venv\Scripts\Activate.ps1
```

### Paso 3: Instalar dependencias principales

```bash
# Una vez activado el venv, deberías ver (.venv) en el prompt

# Instalar dependencias principales (puede tomar varios minutos)
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

**Nota:** Esta instalación puede tomar 5-10 minutos dependiendo de tu conexión.

### Paso 4: Instalar dependencias de testing

```bash
# Instalar dependencias específicas para tests
python -m pip install -r requirements-test.txt
```

### Paso 5: Verificar instalación

```bash
# Verificar que pytest está instalado
python -m pytest --version

# Debería mostrar algo como: pytest 8.4.2

# Verificar que sqlalchemy está instalado
python -c "import sqlalchemy; print('SQLAlchemy:', sqlalchemy.__version__)"

# Verificar que aiosqlite está instalado
python -c "import aiosqlite; print('aiosqlite OK')"
```

### Paso 6: Ejecutar tests de validación

```bash
# Ejecutar TODOS los tests de validación (50+ tests)
python -m pytest tests/test_infrastructure_validation.py -v

# O ejecutar solo un test simple primero
python -m pytest tests/test_infrastructure_validation.py::test_pytest_is_working -v

# O ejecutar con más detalle
python -m pytest tests/test_infrastructure_validation.py -vv -s
```

### Resultado Esperado

Deberías ver algo como:

```
================================================== test session starts ==================================================
collected 50 items

tests/test_infrastructure_validation.py::test_pytest_is_working PASSED                                           [  2%]
tests/test_infrastructure_validation.py::test_pytest_markers_registered PASSED                                   [  4%]
tests/test_infrastructure_validation.py::test_unit_marker PASSED                                                 [  6%]
tests/test_infrastructure_validation.py::test_integration_marker PASSED                                          [  8%]
tests/test_infrastructure_validation.py::test_db_engine_fixture PASSED                                          [ 10%]
tests/test_infrastructure_validation.py::test_db_session_fixture PASSED                                         [ 12%]
...
tests/test_infrastructure_validation.py::test_infrastructure_summary PASSED                                     [100%]

====================================== 50 passed in 5.23s ===============================================
```

---

## Comandos Rápidos (Resumen)

```bash
# Desde el directorio raíz del proyecto
cd "g:/Mi unidad/PSU-IA/Q2/TF1/src/backend"

# Activar venv
source ../.venv/Scripts/activate

# Instalar todo
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install -r requirements-test.txt

# Validar
python -m pytest tests/test_infrastructure_validation.py -v
```

---

## Troubleshooting

### Error: "No module named pytest"
```bash
python -m pip install pytest pytest-asyncio
```

### Error: "No module named sqlalchemy"
```bash
python -m pip install -r requirements.txt
```

### Error: "No module named aiosqlite"
```bash
python -m pip install aiosqlite
```

### Error: "command not found: pytest"
```bash
# Usar python -m pytest en lugar de solo pytest
python -m pytest tests/test_infrastructure_validation.py -v
```

### Tests fallan con errores de import
```bash
# Asegúrate de estar en el directorio backend
pwd  # Debería mostrar: .../PSU-IA/Q2/TF1/src/backend

# Y que el venv esté activado
which python  # Debería mostrar: .../.venv/Scripts/python
```

---

## Información Adicional

### Archivos importantes creados:
- `pytest.ini` - Configuración de pytest
- `requirements-test.txt` - Dependencias de testing
- `tests/conftest.py` - Fixtures globales
- `tests/test_infrastructure_validation.py` - 50+ tests de validación
- `tests/README.md` - Documentación completa
- `tests/VALIDATION.md` - Checklist de validación

### Estado actual:
- ✅ Estructura de tests creada
- ✅ Fixtures implementadas
- ✅ Tests de validación escritos
- ⏳ Pendiente: Instalar dependencias y ejecutar tests

### Próximos pasos después de validación:
Una vez que los tests de validación pasen:
- FASE 2: Implementar tests unitarios
- FASE 3: Implementar tests de integración

---

## Contacto

Si encuentras algún error durante la instalación o ejecución:
1. Copia el mensaje de error completo
2. Verifica que estás en el directorio correcto
3. Verifica que el venv está activado
4. Revisa la sección de Troubleshooting arriba
