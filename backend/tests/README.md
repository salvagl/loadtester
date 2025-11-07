# LoadTester - Test Suite

## Descripción

Suite completa de tests unitarios e integración para el proyecto LoadTester.

## Estructura

```
tests/
├── README.md                              # Este archivo
├── conftest.py                            # Fixtures globales de pytest
├── test_infrastructure_validation.py     # Tests de validación de infraestructura
├── fixtures/                              # Datos de prueba reutilizables
│   ├── openapi_specs.py                  # Especificaciones OpenAPI
│   └── mock_data.py                      # Factory functions para datos mock
├── unit/                                  # Tests unitarios
│   └── (tests individuales de componentes)
└── integration/                           # Tests de integración
    └── (tests de flujos completos)
```

## Requisitos

### Dependencias de Testing

Las dependencias de testing están en `requirements-test.txt`:

- pytest >= 7.4.3
- pytest-asyncio >= 0.21.1
- pytest-cov >= 4.1.0
- pytest-mock >= 3.12.0
- aiosqlite >= 0.19.0
- httpx >= 0.25.2

### Instalación

#### Opción 1: Manual

```bash
# Desde el directorio backend/
pip install -r requirements.txt
pip install -r requirements-test.txt
```

#### Opción 2: Script automático

**Windows:**
```bash
cd backend
run_tests.bat
```

**Linux/Mac:**
```bash
cd backend
chmod +x run_tests.sh
./run_tests.sh
```

## Ejecutar Tests

### Todos los tests

```bash
cd backend
python -m pytest tests/ -v
```

### Solo validación de infraestructura

```bash
python -m pytest tests/test_infrastructure_validation.py -v
```

### Solo tests unitarios

```bash
python -m pytest tests/unit/ -v -m unit
```

### Solo tests de integración

```bash
python -m pytest tests/integration/ -v -m integration
```

### Con cobertura de código

```bash
python -m pytest tests/ --cov=loadtester --cov-report=html
```

### Modos de ejecución

```bash
# Verbose (detallado)
pytest tests/ -v

# Muy verbose (máximo detalle)
pytest tests/ -vv

# Con output de prints
pytest tests/ -s

# Solo el primer fallo
pytest tests/ -x

# Último test que falló
pytest tests/ --lf

# Tests que fallaron seguidos de todos
pytest tests/ --ff
```

## Validación de Infraestructura

Antes de escribir tests, ejecuta la validación de infraestructura:

```bash
python -m pytest tests/test_infrastructure_validation.py -v
```

Este test verifica:
- ✓ Pytest funciona correctamente
- ✓ Marcadores custom registrados
- ✓ Fixtures de BD en memoria funcionan
- ✓ Fixtures de servicios mock funcionan
- ✓ Fixtures de configuración disponibles
- ✓ Directorios temporales se crean
- ✓ Fixtures de OpenAPI specs cargadas
- ✓ Factory functions de datos mock funcionan

## Fixtures Disponibles

### Base de Datos

```python
@pytest.mark.asyncio
async def test_example(db_session):
    # db_session: AsyncSession de SQLite en memoria
    result = await db_session.execute(...)
```

### Servicios Mock

```python
def test_example(mock_ai_client, mock_k6_runner):
    # mock_ai_client: Mock de AIClientInterface
    # mock_k6_runner: Mock de K6RunnerService
    response = await mock_ai_client.chat_completion(...)
```

### Configuración

```python
def test_example(degradation_settings, app_settings):
    # degradation_settings: Dict con configuración de degradación
    # app_settings: Dict con configuración de aplicación
    threshold = degradation_settings["stop_error_threshold"]
```

### Directorios Temporales

```python
def test_example(temp_report_dir, temp_data_dir):
    # temp_report_dir: Path a directorio temporal para reportes
    # temp_data_dir: Path a directorio temporal para datos
    report_path = temp_report_dir + "/report.pdf"
```

## Datos de Prueba

### OpenAPI Specs

```python
from tests.fixtures.openapi_specs import (
    VALID_OPENAPI_JSON,
    PETSTORE_OPENAPI_SPEC,
    INVALID_OPENAPI_MISSING_INFO
)

def test_parser():
    spec = json.loads(VALID_OPENAPI_JSON)
    # ...
```

### Mock Data Factories

```python
from tests.fixtures.mock_data import (
    create_mock_api,
    create_mock_endpoint,
    create_mock_test_scenario
)

def test_scenario():
    endpoint = create_mock_endpoint(
        endpoint_name="GET /users",
        expected_volumetry=100
    )
    # ...
```

## Marcadores (Markers)

Los tests pueden marcarse con:

- `@pytest.mark.unit` - Test unitario
- `@pytest.mark.integration` - Test de integración
- `@pytest.mark.slow` - Test lento
- `@pytest.mark.requires_db` - Requiere BD
- `@pytest.mark.requires_mock` - Requiere mocks

Ejemplo:

```python
@pytest.mark.unit
@pytest.mark.requires_mock
def test_mock_service(mock_k6_runner):
    # ...
```

## Configuración de Pytest

La configuración está en `pytest.ini`:

- **testpaths**: `tests/`
- **python_files**: `test_*.py`
- **asyncio_mode**: `auto` (detecta tests async automáticamente)
- **addopts**: `-v --strict-markers --tb=short`

## Troubleshooting

### Error: "No module named pytest"

```bash
pip install -r requirements-test.txt
```

### Error: "ModuleNotFoundError: No module named 'sqlalchemy'"

```bash
pip install -r requirements.txt
```

### Error: "No module named 'aiosqlite'"

```bash
pip install aiosqlite
```

### Tests muy lentos

```bash
# Ejecutar solo tests rápidos
pytest tests/ -m "not slow"
```

### Ver logs de SQLAlchemy

```bash
pytest tests/ --log-cli-level=DEBUG
```

## Buenas Prácticas

1. **Aislamiento**: Cada test debe ser independiente
2. **Cleanup**: Usar fixtures que limpian automáticamente
3. **Nomenclatura**: `test_<funcion>_<escenario>_<resultado_esperado>`
4. **Marcadores**: Usar marcadores apropiados
5. **Docstrings**: Documentar qué testea cada test
6. **Asserts**: Usar asserts descriptivos

Ejemplo:

```python
@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_api_with_valid_data_succeeds(db_session):
    """Test that creating an API with valid data succeeds."""
    # Arrange
    api = create_mock_api(api_name="Test API")

    # Act
    db_session.add(api)
    await db_session.commit()

    # Assert
    assert api.api_id is not None
    assert api.api_name == "Test API"
```

## Estado Actual

### FASE 1: Infraestructura ✅ COMPLETADA

- [x] Estructura de directorios
- [x] Configuración de pytest
- [x] Fixtures globales
- [x] Fixtures de BD en memoria
- [x] Mocks de servicios
- [x] Fixtures de OpenAPI specs
- [x] Factory functions de datos mock
- [x] Tests de validación

### FASE 2: Tests Unitarios (Próximo)

- [ ] test_openapi_parser.py
- [ ] test_mock_data_generator.py
- [ ] test_scenario_generator.py
- [ ] test_degradation_detection.py
- [ ] test_k6_script_generator.py
- [ ] test_pdf_generator.py
- [ ] test_repositories.py

### FASE 3: Tests de Integración (Pendiente)

- [ ] test_openapi_flow.py
- [ ] test_scenario_flow.py
- [ ] test_job_execution_flow.py
- [ ] test_report_generation_flow.py
- [ ] test_api_endpoints.py
- [ ] test_database_integration.py

## Documentación Completa

Ver documentación completa en:
- [Estrategia de Testing](../../../docs/testing_strategy.md)
- [Quick Reference](../../../docs/testing_quick_reference.md)
