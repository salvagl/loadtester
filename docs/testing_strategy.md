# Estrategia de Testing - LoadTester Application

**Proyecto:** LoadTester - Automated API Load Testing
**Rama de desarrollo:** feat/testing
**Fecha:** 2025-11-07
**Objetivo:** Implementar suite completa de tests unitarios e integración sin afectar la aplicación existente

---

## 1. PRINCIPIOS FUNDAMENTALES

### 1.1 Seguridad del Proyecto
- ✅ Todos los cambios se realizan en rama `feat/testing`
- ✅ NO modificar código de producción existente
- ✅ Tests deben ser independientes y no afectar estado global
- ✅ Usar BD SQLite en memoria para tests de integración
- ✅ Mockear servicios externos (K6, IA)

### 1.2 Alcance del Proyecto
**INCLUIDO:**
- Tests unitarios de componentes core
- Tests de integración de flujos completos
- Mocks de servicios externos (K6, IA)
- BD en memoria (SQLite in-memory)

**EXCLUIDO:**
- Tests end-to-end con K6 real
- Tests de performance de LoadTester
- Tests de UI (Streamlit frontend)

---

## 2. ARQUITECTURA DE TESTING

### 2.1 Estructura de Directorios

```
backend/
├── loadtester/
│   ├── domain/
│   ├── infrastructure/
│   └── presentation/
└── tests/
    ├── __init__.py
    ├── conftest.py                 # Fixtures globales y configuración pytest
    ├── fixtures/
    │   ├── __init__.py
    │   ├── openapi_specs.py        # Specs OpenAPI de ejemplo
    │   ├── mock_data.py            # Datos mock para tests
    │   └── test_data.py            # Datos de prueba estructurados
    ├── unit/
    │   ├── __init__.py
    │   ├── test_openapi_parser.py          # Tests LocalOpenAPIParser
    │   ├── test_mock_data_generator.py     # Tests MockDataGeneratorService
    │   ├── test_scenario_generator.py      # Tests creación de escenarios
    │   ├── test_degradation_detection.py   # Tests detección degradación
    │   ├── test_k6_script_generator.py     # Tests generación scripts K6
    │   ├── test_pdf_generator.py           # Tests generación PDF
    │   └── test_repositories.py            # Tests repositorios individuales
    └── integration/
        ├── __init__.py
        ├── test_openapi_flow.py            # Flujo OpenAPI → Endpoints
        ├── test_scenario_flow.py           # Flujo generación escenarios
        ├── test_job_execution_flow.py      # Flujo ejecución jobs (K6 mock)
        ├── test_report_generation_flow.py  # Flujo generación reportes
        ├── test_api_endpoints.py           # Tests API REST completa
        └── test_database_integration.py    # Tests integración con BD
```

### 2.2 Herramientas y Frameworks

- **pytest**: Framework principal de testing
- **pytest-asyncio**: Soporte para tests asíncronos
- **pytest-mock**: Mocking y spying
- **pytest-cov**: Cobertura de código
- **SQLAlchemy + SQLite**: BD en memoria para tests
- **faker**: Generación de datos realistas
- **httpx**: Cliente HTTP para tests de API

---

## 3. TESTS UNITARIOS

### 3.1 OpenAPI Parser (`LocalOpenAPIParser`)

**Archivo:** `tests/unit/test_openapi_parser.py`

**Casos de prueba:**

```python
class TestLocalOpenAPIParser:
    # Validación de specs
    - test_validate_spec_valid_json()
    - test_validate_spec_valid_yaml()
    - test_validate_spec_invalid_format()
    - test_validate_spec_missing_required_fields()

    # Parsing
    - test_parse_openapi_spec_json()
    - test_parse_openapi_spec_yaml()
    - test_parse_openapi_spec_with_bom()
    - test_parse_openapi_spec_invalid()

    # Extracción de endpoints
    - test_extract_endpoints_simple()
    - test_extract_endpoints_multiple_methods()
    - test_extract_endpoints_with_parameters()
    - test_extract_endpoints_empty_spec()

    # Resolución de referencias
    - test_resolve_ref_simple()
    - test_resolve_ref_nested()
    - test_resolve_ref_circular()
    - test_resolve_schema_refs_in_request_body()
    - test_resolve_schema_refs_in_parameters()

    # Obtención de schemas
    - test_get_endpoint_schema_with_refs()
    - test_get_endpoint_schema_nonexistent()
```

**Mocks necesarios:**
- No requiere mocks externos (parser local)

---

### 3.2 Mock Data Generator (`MockDataGeneratorService`)

**Archivo:** `tests/unit/test_mock_data_generator.py`

**Casos de prueba:**

```python
class TestMockDataGeneratorService:
    # Generación según tipos
    - test_generate_faker_value_integer()
    - test_generate_faker_value_email()
    - test_generate_faker_value_phone()
    - test_generate_faker_value_date()
    - test_generate_faker_value_url()
    - test_generate_faker_value_name_variations()

    # Generación desde schema
    - test_generate_body_from_schema_simple_object()
    - test_generate_body_from_schema_nested_object()
    - test_generate_body_from_schema_array()
    - test_generate_body_from_schema_with_required_fields()
    - test_generate_body_from_schema_with_enums()

    # Análisis de endpoints
    - test_analyze_endpoint_requirements_path_params()
    - test_analyze_endpoint_requirements_query_params()
    - test_analyze_endpoint_requirements_request_body()

    # Generación de datos mock
    - test_generate_mock_data_count()
    - test_generate_mock_data_unique_emails()
    - test_generate_mock_data_for_post_endpoint()
    - test_generate_mock_data_for_get_endpoint()

    # Casos edge
    - test_generate_mock_data_empty_schema()
    - test_generate_mock_data_complex_nested_structure()
```

**Mocks necesarios:**
- Mock de `AIClientInterface` (para evitar llamadas reales a IA)

---

### 3.3 Scenario Generator

**Archivo:** `tests/unit/test_scenario_generator.py`

**Casos de prueba:**

```python
class TestScenarioGenerator:
    # Cálculo de cargas
    - test_calculate_load_percentages()
    - test_calculate_users_for_percentage()
    - test_calculate_volumetry_for_percentage()
    - test_minimum_load_values()  # Nunca < 1

    # Creación de escenarios
    - test_create_incremental_scenarios_count()  # Verifica 6 escenarios
    - test_create_incremental_scenarios_warmup()
    - test_create_incremental_scenarios_load_progression()
    - test_create_incremental_scenarios_naming()

    # Configuración de escenarios
    - test_scenario_duration_configuration()
    - test_scenario_ramp_up_down()
    - test_scenario_test_data_assignment()
```

**Mocks necesarios:**
- Mock de `TestScenarioRepository`
- Endpoint fixtures

---

### 3.4 Degradation Detection

**Archivo:** `tests/unit/test_degradation_detection.py`

**Casos de prueba:**

```python
class TestDegradationDetection:
    # Detección por tasa de errores
    - test_should_stop_high_error_rate()
    - test_should_not_stop_acceptable_error_rate()
    - test_should_stop_at_threshold()

    # Detección por tiempo de respuesta
    - test_should_stop_response_time_degradation()
    - test_should_not_stop_acceptable_response_time()
    - test_should_stop_at_multiplier_threshold()

    # Casos edge
    - test_should_stop_no_baseline()
    - test_should_stop_null_result()
    - test_should_not_stop_first_scenario()

    # Configuración de umbrales
    - test_custom_degradation_settings()
```

**Mocks necesarios:**
- `TestResult` fixtures con diferentes métricas
- Configuración de degradation_settings

---

### 3.5 K6 Script Generator

**Archivo:** `tests/unit/test_k6_script_generator.py`

**Casos de prueba:**

```python
class TestK6ScriptGenerator:
    # Generación básica
    - test_generate_k6_script_structure()
    - test_generate_k6_script_imports()
    - test_generate_k6_script_options()

    # Configuración de VUs y duración
    - test_script_vus_configuration()
    - test_script_duration_configuration()
    - test_script_ramp_stages()

    # Autenticación
    - test_script_bearer_token_auth()
    - test_script_api_key_auth()
    - test_script_no_auth()

    # Endpoints y datos
    - test_script_endpoint_configuration()
    - test_script_test_data_inclusion()
    - test_script_path_params_replacement()
    - test_script_query_params_addition()
    - test_script_request_body()

    # HTTP methods
    - test_script_get_request()
    - test_script_post_request()
    - test_script_put_request()
    - test_script_delete_request()

    # Validación sintáctica
    - test_script_valid_javascript_syntax()
```

**Mocks necesarios:**
- Endpoint fixtures con diferentes configuraciones
- Datos mock de prueba

---

### 3.6 PDF Generator (funciones auxiliares)

**Archivo:** `tests/unit/test_pdf_generator.py`

**Casos de prueba:**

```python
class TestPDFGenerator:
    # Formateo de datos
    - test_format_metrics_for_table()
    - test_format_duration_string()
    - test_clean_markdown_from_text()

    # Cálculos
    - test_calculate_test_duration()
    - test_calculate_success_rate()

    # Generación de estructuras
    - test_build_toc_data()
    - test_build_config_table()
    - test_build_results_table()

    # Casos edge
    - test_handle_missing_data()
    - test_handle_null_timestamps()
```

**Mocks necesarios:**
- `TestResult` fixtures
- Job fixtures

---

### 3.7 Repositories

**Archivo:** `tests/unit/test_repositories.py`

**Casos de prueba:**

```python
class TestRepositories:
    # Para cada repositorio (API, Endpoint, Job, etc.)
    - test_create()
    - test_get_by_id()
    - test_get_all()
    - test_update()
    - test_delete()
    - test_get_by_filters()

    # Casos específicos
    - test_job_repository_get_running_jobs()
    - test_endpoint_repository_get_by_api()
    - test_scenario_repository_get_by_endpoint()
```

**Mocks necesarios:**
- SQLAlchemy session en memoria

---

## 4. TESTS DE INTEGRACIÓN

### 4.1 Flujo OpenAPI → Endpoints

**Archivo:** `tests/integration/test_openapi_flow.py`

**Casos de prueba:**

```python
class TestOpenAPIFlow:
    - test_complete_openapi_parsing_flow()
        # Cargar spec → Validar → Parsear → Extraer endpoints → Persistir API → Persistir Endpoints

    - test_openapi_flow_with_petstore_api()
    - test_openapi_flow_with_complex_refs()
    - test_openapi_flow_validation_failure()
    - test_openapi_flow_endpoint_filtering()
```

**Dependencias:**
- BD SQLite en memoria
- LocalOpenAPIParser
- API y Endpoint repositories

---

### 4.2 Flujo Generación de Escenarios

**Archivo:** `tests/integration/test_scenario_flow.py`

**Casos de prueba:**

```python
class TestScenarioFlow:
    - test_complete_scenario_generation_flow()
        # Endpoint → Generar mock data → Crear 6 escenarios → Persistir

    - test_scenario_generation_with_custom_data()
    - test_scenario_generation_multiple_endpoints()
    - test_scenario_mock_data_sufficient_count()
    - test_scenario_data_uniqueness()
```

**Dependencias:**
- BD en memoria
- MockDataGeneratorService (con AI mock)
- Scenario repository

---

### 4.3 Flujo Jobs y Ejecución (K6 Mockeado)

**Archivo:** `tests/integration/test_job_execution_flow.py`

**Casos de prueba:**

```python
class TestJobExecutionFlow:
    - test_complete_job_execution_flow()
        # Create job → Execute scenarios (K6 mock) → Collect results → Update job status

    - test_job_creation_and_validation()
    - test_job_concurrent_limit()
    - test_job_progress_tracking()
    - test_job_execution_with_degradation_stop()
    - test_job_failure_handling()
    - test_job_cancellation()
```

**Mocks necesarios:**
- **CRÍTICO:** Mock completo de K6RunnerService
- Mock de resultados K6 realistas
- BD en memoria

---

### 4.4 Flujo Generación de Reportes

**Archivo:** `tests/integration/test_report_generation_flow.py`

**Casos de prueba:**

```python
class TestReportGenerationFlow:
    - test_complete_report_generation_flow()
        # Results → Generate PDF → Verify file exists → Verify content

    - test_report_with_multiple_endpoints()
    - test_report_with_degradation_detected()
    - test_report_with_missing_data()
    - test_report_file_naming()
```

**Dependencias:**
- PDFGeneratorService
- Directorio temporal para PDFs
- TestResult fixtures

---

### 4.5 API REST Endpoints

**Archivo:** `tests/integration/test_api_endpoints.py`

**Casos de prueba:**

```python
class TestAPIEndpoints:
    # POST /api/v1/load-test
    - test_create_load_test_success()
    - test_create_load_test_invalid_config()
    - test_create_load_test_concurrent_limit()

    # GET /api/v1/status/{job_id}
    - test_get_job_status_pending()
    - test_get_job_status_running()
    - test_get_job_status_finished()
    - test_get_job_status_failed()
    - test_get_job_status_not_found()

    # GET /api/v1/report/{job_id}
    - test_download_report_success()
    - test_download_report_not_ready()
    - test_download_report_not_found()

    # POST /api/v1/openapi/validate
    - test_validate_openapi_spec_valid()
    - test_validate_openapi_spec_invalid()

    # POST /api/v1/openapi/parse
    - test_parse_openapi_spec()

    # GET /api/v1/health
    - test_health_check()
```

**Dependencias:**
- FastAPI TestClient
- BD en memoria
- Todos los servicios mockeados

---

### 4.6 Integración con Base de Datos

**Archivo:** `tests/integration/test_database_integration.py`

**Casos de prueba:**

```python
class TestDatabaseIntegration:
    # Relaciones entre entidades
    - test_api_endpoint_relationship()
    - test_endpoint_scenario_relationship()
    - test_scenario_execution_relationship()
    - test_execution_result_relationship()

    # Cascadas y deletes
    - test_delete_api_cascades_endpoints()
    - test_delete_endpoint_cascades_scenarios()

    # Transacciones
    - test_transaction_rollback_on_error()
    - test_transaction_commit_on_success()

    # Queries complejas
    - test_get_all_results_for_job()
    - test_get_running_jobs_query()
```

**Dependencias:**
- BD SQLite en memoria
- Todos los modelos y repositorios

---

## 5. FIXTURES Y CONFIGURACIÓN

### 5.1 conftest.py (Fixtures Globales)

```python
# BD en memoria
@pytest.fixture
def db_session():
    """SQLAlchemy session con SQLite en memoria"""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()

# Servicios mockeados
@pytest.fixture
def mock_ai_client():
    """Mock de AIClientInterface"""
    pass

@pytest.fixture
def mock_k6_runner():
    """Mock de K6RunnerServiceInterface"""
    pass

@pytest.fixture
def mock_k6_generator():
    """Mock de K6ScriptGeneratorServiceInterface"""
    pass

# Configuración
@pytest.fixture
def degradation_settings():
    """Configuración de degradación estándar"""
    return {
        "degradation_response_time_multiplier": 5.0,
        "degradation_error_rate_threshold": 0.5,
        "stop_error_threshold": 0.6,
        "max_concurrent_jobs": 1,
        "default_test_duration": 60
    }

# Directorios temporales
@pytest.fixture
def temp_report_dir(tmp_path):
    """Directorio temporal para reportes PDF"""
    report_dir = tmp_path / "reports"
    report_dir.mkdir()
    return report_dir
```

### 5.2 fixtures/openapi_specs.py

```python
# Especificaciones OpenAPI de ejemplo
VALID_OPENAPI_JSON = {...}
VALID_OPENAPI_YAML = """..."""
INVALID_OPENAPI_MISSING_INFO = {...}
PETSTORE_OPENAPI_SPEC = {...}
COMPLEX_OPENAPI_WITH_REFS = {...}
```

### 5.3 fixtures/mock_data.py

```python
# Datos mock para tests
def create_mock_endpoint(...):
    """Crea Endpoint de prueba"""
    pass

def create_mock_test_result(...):
    """Crea TestResult de prueba"""
    pass

def create_mock_k6_results(...):
    """Crea resultados K6 simulados"""
    pass
```

---

## 6. CONFIGURACIÓN DE PYTEST

### 6.1 pytest.ini

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
asyncio_mode = auto
markers =
    unit: Unit tests
    integration: Integration tests
    slow: Slow running tests
```

### 6.2 Ejecución de Tests

```bash
# Todos los tests
pytest

# Solo unitarios
pytest tests/unit -m unit

# Solo integración
pytest tests/integration -m integration

# Con cobertura
pytest --cov=loadtester --cov-report=html

# Verbose
pytest -v

# Con output completo
pytest -s
```

---

## 7. MOCKS CRÍTICOS

### 7.1 Mock de K6RunnerService

**IMPORTANTE:** Este es el mock más crítico del proyecto

```python
class MockK6Runner:
    async def execute_k6_script(self, script_content, execution_id):
        """Retorna resultados K6 simulados realistas"""
        return {
            "metrics": {
                "http_req_duration": {
                    "avg": 150.5,
                    "min": 50.2,
                    "max": 500.8,
                    "p(95)": 300.0,
                    "p(99)": 450.0
                },
                "http_reqs": {
                    "count": 1000,
                    "rate": 16.67
                },
                "http_req_failed": {
                    "count": 10,
                    "rate": 0.01
                },
                "data_sent": {"count": 102400},
                "data_received": {"count": 512000}
            },
            "logs": ["K6 execution log..."]
        }
```

### 7.2 Mock de AIClientInterface

```python
class MockAIClient:
    async def chat_completion(self, messages, max_tokens):
        """Retorna respuesta simulada de IA"""
        # Para mock data generation, retornar JSON válido
        return '[{"path_params": {"id": 1}, "body": {"name": "Test"}}]'
```

---

## 8. CASOS EDGE Y ESCENARIOS ESPECIALES

### 8.1 Casos Edge a Cubrir

1. **OpenAPI Parser**
   - Specs con codificación BOM
   - YAML con caracteres especiales
   - Referencias circulares
   - Schemas vacíos

2. **Mock Data Generator**
   - Emails únicos en grandes volúmenes (>1000)
   - Arrays con minItems/maxItems
   - Objetos anidados profundos (>5 niveles)
   - Enums con valores especiales

3. **Scenario Generator**
   - Volumetría muy baja (< 10 req/min)
   - Usuarios concurrentes = 1
   - Duración de test = 0

4. **Degradation Detection**
   - Primer escenario con errores
   - Baseline = null
   - Umbrales en 0

5. **Job Execution**
   - Cancelación durante ejecución
   - Timeout de K6
   - Fallo en medio de escenario

6. **PDF Generation**
   - Datos faltantes en resultados
   - Timestamps null
   - Endpoints sin nombre

---

## 9. CHECKLIST DE IMPLEMENTACIÓN

### Fase 1: Configuración Base
- [ ] Crear estructura de directorios `tests/`
- [ ] Configurar `pytest.ini`
- [ ] Crear `conftest.py` con fixtures básicas
- [ ] Crear fixtures de OpenAPI specs
- [ ] Crear fixtures de datos mock

### Fase 2: Tests Unitarios (Orden de implementación)
- [ ] test_openapi_parser.py
- [ ] test_mock_data_generator.py
- [ ] test_scenario_generator.py
- [ ] test_degradation_detection.py
- [ ] test_k6_script_generator.py
- [ ] test_pdf_generator.py (funciones auxiliares)
- [ ] test_repositories.py

### Fase 3: Tests de Integración
- [ ] test_openapi_flow.py
- [ ] test_scenario_flow.py
- [ ] test_job_execution_flow.py (con K6 mock)
- [ ] test_report_generation_flow.py
- [ ] test_api_endpoints.py
- [ ] test_database_integration.py

### Fase 4: Validación y Limpieza
- [ ] Ejecutar todos los tests
- [ ] Verificar cobertura de código
- [ ] Revisar y limpiar código de tests
- [ ] Documentar hallazgos
- [ ] Preparar PR para merge

---

## 10. CRITERIOS DE ÉXITO

### Criterios Técnicos
- ✅ Todos los tests pasan (100% success rate)
- ✅ No se modifica código de producción
- ✅ Tests son independientes y repetibles
- ✅ BD en memoria funciona correctamente
- ✅ Mocks de K6 y IA funcionan correctamente
- ✅ Tests se ejecutan en < 30 segundos (total)

### Criterios de Cobertura
- ✅ OpenAPI Parser: Casos principales y edge cases
- ✅ Mock Data Generator: Todos los tipos de datos
- ✅ Scenario Generator: Cálculos y creación
- ✅ Degradation Detection: Umbrales y lógica
- ✅ Flujos de integración completos
- ✅ API endpoints principales

---

## 11. NOTAS IMPORTANTES

### 11.1 Precauciones
- **NUNCA modificar código de producción** en `loadtester/`
- **SIEMPRE** usar BD en memoria para tests
- **SIEMPRE** mockear K6 (no ejecutar contenedor real)
- **SIEMPRE** mockear servicios de IA
- **VERIFICAR** que todos los tests limpian recursos después de ejecutar

### 11.2 Debugging
- Usar `pytest -s` para ver prints
- Usar `pytest --pdb` para debugging interactivo
- Usar `pytest -v` para output detallado
- Revisar logs de SQLAlchemy si hay problemas con BD

### 11.3 Mantenimiento
- Actualizar fixtures cuando cambien modelos
- Mantener mocks sincronizados con interfaces reales
- Revisar tests cuando se añadan features nuevas
- Documentar casos edge nuevos que se descubran

---

**Fin de Estrategia de Testing**

Esta estrategia se implementará completamente en la rama `feat/testing` sin afectar el código de producción.
