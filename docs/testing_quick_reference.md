# Quick Reference - Testing Strategy

## Resumen Ejecutivo

**Proyecto:** Suite completa de tests para LoadTester
**Rama:** `feat/testing`
**Estado:** Estrategia documentada - Listo para implementación

---

## Tests a Implementar

### Tests Unitarios (7 archivos)
1. `test_openapi_parser.py` - Parser de especificaciones OpenAPI
2. `test_mock_data_generator.py` - Generación de datos mock
3. `test_scenario_generator.py` - Creación de escenarios de carga
4. `test_degradation_detection.py` - Detección de degradación
5. `test_k6_script_generator.py` - Generación de scripts K6
6. `test_pdf_generator.py` - Funciones auxiliares de PDF
7. `test_repositories.py` - Repositorios individuales

### Tests de Integración (6 archivos)
1. `test_openapi_flow.py` - Flujo OpenAPI completo
2. `test_scenario_flow.py` - Flujo generación escenarios
3. `test_job_execution_flow.py` - Flujo ejecución jobs (K6 mock)
4. `test_report_generation_flow.py` - Flujo generación reportes
5. `test_api_endpoints.py` - API REST completa
6. `test_database_integration.py` - Integración con BD

**Total:** 13 archivos de tests + fixtures + configuración

---

## Mocks Críticos

### 1. K6RunnerService (CRÍTICO)
```python
# Retorna resultados K6 simulados realistas
{
    "metrics": {
        "http_req_duration": {"avg": 150.5, "p(95)": 300.0, ...},
        "http_reqs": {"count": 1000, "rate": 16.67},
        "http_req_failed": {"count": 10, "rate": 0.01},
        ...
    }
}
```

### 2. AIClientInterface
```python
# Retorna JSON válido para mock data generation
'[{"path_params": {"id": 1}, "body": {"name": "Test"}}]'
```

### 3. SQLite en Memoria
```python
# BD limpia para cada test
engine = create_engine("sqlite:///:memory:")
```

---

## Comandos Principales

```bash
# Cambiar a rama de testing
git checkout feat/testing

# Ejecutar todos los tests
pytest

# Solo tests unitarios
pytest tests/unit -m unit

# Solo tests de integración
pytest tests/integration -m integration

# Con cobertura
pytest --cov=loadtester --cov-report=html

# Verbose
pytest -v -s
```

---

## Estructura de Directorios

```
backend/tests/
├── conftest.py                     # Fixtures globales
├── fixtures/
│   ├── openapi_specs.py           # Specs OpenAPI ejemplo
│   ├── mock_data.py               # Datos mock
│   └── test_data.py               # Datos estructurados
├── unit/                          # 7 archivos
│   ├── test_openapi_parser.py
│   ├── test_mock_data_generator.py
│   ├── test_scenario_generator.py
│   ├── test_degradation_detection.py
│   ├── test_k6_script_generator.py
│   ├── test_pdf_generator.py
│   └── test_repositories.py
└── integration/                   # 6 archivos
    ├── test_openapi_flow.py
    ├── test_scenario_flow.py
    ├── test_job_execution_flow.py
    ├── test_report_generation_flow.py
    ├── test_api_endpoints.py
    └── test_database_integration.py
```

---

## Orden de Implementación

### Fase 1: Configuración (Base)
- [ ] Estructura de directorios
- [ ] pytest.ini
- [ ] conftest.py con fixtures
- [ ] Fixtures de OpenAPI y datos mock

### Fase 2: Tests Unitarios
- [ ] OpenAPI Parser
- [ ] Mock Data Generator
- [ ] Scenario Generator
- [ ] Degradation Detection
- [ ] K6 Script Generator
- [ ] PDF Generator
- [ ] Repositories

### Fase 3: Tests de Integración
- [ ] OpenAPI Flow
- [ ] Scenario Flow
- [ ] Job Execution Flow (K6 mock)
- [ ] Report Generation Flow
- [ ] API Endpoints
- [ ] Database Integration

### Fase 4: Validación
- [ ] Ejecutar todos los tests
- [ ] Verificar cobertura
- [ ] Limpiar código
- [ ] Preparar PR

---

## Principios Fundamentales

### ✅ HACER
- Trabajar en rama `feat/testing`
- Usar BD SQLite en memoria
- Mockear K6 y servicios IA
- Tests independientes y repetibles
- Limpiar recursos después de tests

### ❌ NO HACER
- Modificar código de producción en `loadtester/`
- Usar BD real para tests
- Ejecutar K6 contenedor real
- Llamadas reales a servicios IA
- Tests end-to-end

---

## Criterios de Éxito

- ✅ Todos los tests pasan (100%)
- ✅ No se modifica código de producción
- ✅ Tests independientes y repetibles
- ✅ BD en memoria funciona
- ✅ Mocks de K6 y IA funcionan
- ✅ Tests ejecutan en < 30 segundos

---

## Fixtures Clave

```python
# BD en memoria
@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()

# Mock K6
@pytest.fixture
def mock_k6_runner():
    mock = MockK6Runner()
    mock.execute_k6_script = AsyncMock(return_value=MOCK_K6_RESULTS)
    return mock

# Mock IA
@pytest.fixture
def mock_ai_client():
    mock = MockAIClient()
    mock.chat_completion = AsyncMock(return_value='[{...}]')
    return mock

# Configuración degradación
@pytest.fixture
def degradation_settings():
    return {
        "degradation_response_time_multiplier": 5.0,
        "degradation_error_rate_threshold": 0.5,
        "stop_error_threshold": 0.6,
        "max_concurrent_jobs": 1,
        "default_test_duration": 60
    }
```

---

## Casos Edge Importantes

1. **OpenAPI Parser**: Specs con BOM, referencias circulares, schemas vacíos
2. **Mock Data Generator**: Emails únicos >1000, objetos anidados profundos
3. **Scenario Generator**: Volumetría < 10, usuarios = 1
4. **Degradation Detection**: Baseline null, primer escenario con errores
5. **Job Execution**: Cancelación durante ejecución, timeout K6
6. **PDF Generation**: Datos faltantes, timestamps null

---

## Debugging Tips

```bash
# Ver prints en tests
pytest -s

# Debugging interactivo
pytest --pdb

# Output detallado
pytest -v

# Test específico
pytest tests/unit/test_openapi_parser.py::TestOpenAPIParser::test_validate_spec_valid_json

# Logs de SQLAlchemy
pytest --log-cli-level=DEBUG
```

---

## Documentación Completa

Ver [testing_strategy.md](testing_strategy.md) para documentación completa con:
- Detalles de cada caso de prueba
- Explicación de mocks
- Configuración de pytest
- Checklist de implementación
- Notas de mantenimiento

---

**Última actualización:** 2025-11-07
**Rama:** feat/testing
**Estado:** Listo para comenzar implementación
