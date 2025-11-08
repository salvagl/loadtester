# FASE 3 - Plan de Continuación para Mañana

**Fecha de Creación:** 2025-01-08
**Estado Actual:** 🟡 EN PROGRESO (50% completado)
**Próxima Sesión:** Continuar implementación completa

---

## 📊 Estado Actual al Final de Hoy

### Tests de Integración Implementados

| Archivo | Tests | Pasando | Fallando | Estado |
|---------|-------|---------|----------|--------|
| `test_openapi_flow.py` | 11 | 11 | 0 | ✅ 100% |
| `test_scenario_flow.py` | 11 | 7 | 4 | 🟡 63.6% |
| `test_job_execution_flow.py` | 14 | 14 | 0 | ✅ 100% |
| **TOTAL ACTUAL** | **36** | **32** | **4** | **88.9%** |

### Comando para Ejecutar Tests Actuales
```bash
cd "g:/Mi unidad/PSU-IA/Q2/TF1/src/backend"
source ../.venv/Scripts/activate
python -m pytest tests/integration/ -v
```

### Resultado Actual
```
32 passed, 4 failed, 7 warnings in 19.89s
```

---

## 🐛 PASO 1: Corregir Tests Fallidos (5-10 minutos)

### test_scenario_flow.py - 4 Correcciones Necesarias

#### Corrección 1: test_complete_scenario_generation_flow (línea ~43)

**Ubicación:** `tests/integration/test_scenario_flow.py:43`

**Error:**
```python
TypeError: create_mock_endpoint_post() got an unexpected keyword argument 'endpoint_path'
```

**Código Actual (INCORRECTO):**
```python
endpoint = create_mock_endpoint_post(
    api_id=created_api.api_id,
    endpoint_path="/users",  # ❌ NO EXISTE
    http_method="POST"       # ❌ NO EXISTE
)
```

**Corrección:**
```python
endpoint = create_mock_endpoint_post(
    api_id=created_api.api_id
)
```

---

#### Correcciones 2, 3, 4: generate_mock_data() - Parámetro Incorrecto

**Tests Afectados:**
- `test_scenario_generation_with_custom_data` (línea ~166)
- `test_scenario_mock_data_sufficient_count` (línea ~271)
- `test_scenario_data_uniqueness` (línea ~324)

**Error:**
```python
TypeError: MockDataGeneratorService.generate_mock_data() got an unexpected keyword argument 'endpoint_schema'
```

**Código Actual (INCORRECTO):**
```python
mock_data = await mock_generator.generate_mock_data(
    endpoint=created_endpoint,
    endpoint_schema=schema,  # ❌ PARÁMETRO INCORRECTO
    count=100
)
```

**Corrección (aplicar en las 3 ubicaciones):**
```python
mock_data = await mock_generator.generate_mock_data(
    endpoint=created_endpoint,
    schema=schema,  # ✅ CORRECTO
    count=100
)
```

---

### Verificación Post-Corrección

**Comando:**
```bash
python -m pytest tests/integration/test_scenario_flow.py -v
```

**Resultado Esperado:**
```
11 passed in ~XX seconds
```

**Total tras correcciones:**
```
36 passed, 0 failed
```

---

## 🚀 PASO 2: Implementar Archivos Faltantes

### Archivos Pendientes Según Estrategia Original

Referencia: `docs/testing_strategy.md` - Sección "4. TESTS DE INTEGRACIÓN"

---

### Archivo 4: test_report_generation_flow.py

**Ubicación:** `tests/integration/test_report_generation_flow.py`

**Referencia Estrategia:** Líneas 418-440 de `testing_strategy.md`

**Tests a Implementar (~10-15 tests):**

```python
# Tests Principales
1. test_complete_report_generation_flow()
   # Results → Generate PDF → Verify file exists → Verify content

2. test_report_with_multiple_endpoints()
   # Reporte con resultados de múltiples endpoints

3. test_report_with_degradation_detected()
   # Reporte que incluye detección de degradación

4. test_report_with_missing_data()
   # Manejo de datos faltantes en resultados

5. test_report_file_naming()
   # Verificar convención de nombres de archivo

# Tests de Clasificación de Performance
6. test_report_performance_classification_excellent()
7. test_report_performance_classification_good()
8. test_report_performance_classification_acceptable()
9. test_report_performance_classification_poor()

# Tests de Contenido PDF
10. test_report_contains_metrics_table()
11. test_report_contains_summary_section()
12. test_report_contains_recommendations()

# Edge Cases
13. test_report_with_null_timestamps()
14. test_report_with_zero_requests()
```

**Componentes a Integrar:**
- `ReportGeneratorService` (from `loadtester.infrastructure.external.pdf_generator_service`)
- `TestResultRepository`
- `JobRepository`
- Directorio temporal para PDFs (fixture: `tmp_path`)

**Imports Necesarios:**
```python
from loadtester.infrastructure.external.pdf_generator_service import ReportGeneratorService
from loadtester.infrastructure.repositories.test_result_repository import TestResultRepository
from loadtester.infrastructure.repositories.job_repository import JobRepository
from tests.fixtures.mock_data import create_mock_test_result, create_mock_job
import os
from pathlib import Path
```

---

### Archivo 5: test_api_endpoints.py

**Ubicación:** `tests/integration/test_api_endpoints.py`

**Referencia Estrategia:** Líneas 442-483 de `testing_strategy.md`

**Tests a Implementar (~15-20 tests):**

```python
# POST /api/v1/load-test
1. test_create_load_test_success()
2. test_create_load_test_invalid_config()
3. test_create_load_test_invalid_openapi_spec()
4. test_create_load_test_concurrent_limit()

# GET /api/v1/status/{job_id}
5. test_get_job_status_pending()
6. test_get_job_status_running()
7. test_get_job_status_finished()
8. test_get_job_status_failed()
9. test_get_job_status_not_found()
10. test_get_job_status_with_progress()

# GET /api/v1/report/{job_id}
11. test_download_report_success()
12. test_download_report_not_ready()
13. test_download_report_not_found()

# POST /api/v1/openapi/validate
14. test_validate_openapi_spec_valid_json()
15. test_validate_openapi_spec_valid_yaml()
16. test_validate_openapi_spec_invalid()

# POST /api/v1/openapi/parse
17. test_parse_openapi_spec_success()
18. test_parse_openapi_spec_invalid()

# GET /api/v1/health
19. test_health_check()

# Error Handling
20. test_endpoint_validation_errors()
```

**Componentes a Integrar:**
- FastAPI `TestClient`
- Todos los routers de `loadtester.presentation.api.v1`
- Mocks de servicios (K6Runner, etc.)

**Imports Necesarios:**
```python
from fastapi.testclient import TestClient
from loadtester.presentation.api.main import app
from unittest.mock import AsyncMock, patch
import json
```

**Fixture Necesaria:**
```python
@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)
```

---

### Archivo 6: test_database_integration.py

**Ubicación:** `tests/integration/test_database_integration.py`

**Referencia Estrategia:** Líneas 485-511 de `testing_strategy.md`

**Tests a Implementar (~10-15 tests):**

```python
# Relaciones entre entidades
1. test_api_endpoint_relationship()
   # API tiene múltiples Endpoints

2. test_endpoint_scenario_relationship()
   # Endpoint tiene múltiples Scenarios

3. test_scenario_execution_relationship()
   # Scenario tiene múltiples Executions

4. test_execution_result_relationship()
   # Execution tiene un Result

5. test_job_complete_chain()
   # Job → API → Endpoints → Scenarios → Executions → Results

# Cascadas y Deletes
6. test_delete_api_cascades_endpoints()
7. test_delete_endpoint_cascades_scenarios()
8. test_delete_scenario_cascades_executions()

# Transacciones
9. test_transaction_rollback_on_error()
10. test_transaction_commit_on_success()

# Queries complejas
11. test_get_all_results_for_job()
12. test_get_running_jobs_query()
13. test_get_scenarios_by_endpoint()

# Integridad Referencial
14. test_foreign_key_constraints()
15. test_unique_constraints()
```

**Componentes a Integrar:**
- Todos los repositorios
- Todas las entidades de dominio
- Verificación de cascadas y constraints

**Imports Necesarios:**
```python
from loadtester.domain.entities.domain_entities import (
    API, Endpoint, TestScenario, TestExecution, TestResult, Job
)
from loadtester.infrastructure.repositories import (
    APIRepository, EndpointRepository, TestScenarioRepository,
    TestExecutionRepository, TestResultRepository, JobRepository
)
from sqlalchemy.exc import IntegrityError
import pytest
```

---

## 📋 Orden de Implementación Recomendado

### Sesión Mañana (2-3 horas)

**Prioridad 1: Correcciones (10 min)**
1. ✅ Corregir 4 tests en `test_scenario_flow.py`
2. ✅ Verificar 36/36 passing

**Prioridad 2: Report Generation (45 min)**
3. ✅ Implementar `test_report_generation_flow.py` (10-15 tests)
4. ✅ Ejecutar y corregir errores

**Prioridad 3: Database Integration (30 min)**
5. ✅ Implementar `test_database_integration.py` (10-15 tests)
6. ✅ Ejecutar y corregir errores

**Prioridad 4: API Endpoints (1 hora)**
7. ✅ Implementar `test_api_endpoints.py` (15-20 tests)
8. ✅ Configurar TestClient y mocks
9. ✅ Ejecutar y corregir errores

**Prioridad 5: Validación Final (15 min)**
10. ✅ Ejecutar suite completa de integración
11. ✅ Generar reporte de cobertura
12. ✅ Actualizar documentación final

---

## 🎯 Objetivo Final

### Meta de Tests
- **Archivos:** 6/6 (100%)
- **Tests Totales:** 70-85 tests de integración
- **Pass Rate:** 100%
- **Tiempo Ejecución:** < 60 segundos

### Meta de Cobertura
- ✅ OpenAPI Flow (100%)
- ✅ Scenario Flow (100%)
- ✅ Job Execution Flow (100%)
- ✅ Report Generation Flow (100%)
- ✅ API REST Endpoints (100%)
- ✅ Database Integration (100%)

### Comandos Finales

**Ejecutar todos los tests de integración:**
```bash
python -m pytest tests/integration/ -v
```

**Generar reporte de cobertura:**
```bash
python -m pytest tests/integration/ --cov=loadtester --cov-report=html --cov-report=term
```

**Ver cobertura:**
```bash
# El reporte HTML estará en: htmlcov/index.html
```

---

## 📚 Referencias Importantes

### Documentos de Estrategia
- **Estrategia completa:** `docs/testing_strategy.md`
- **Fixtures disponibles:** `tests/fixtures/mock_data.py`
- **Configuración pytest:** `pytest.ini`
- **Tests unitarios (referencia):** `tests/unit/`

### Ubicaciones de Código de Producción
- **Servicios:** `loadtester/domain/services/`
- **Repositorios:** `loadtester/infrastructure/repositories/`
- **Entidades:** `loadtester/domain/entities/domain_entities.py`
- **API Endpoints:** `loadtester/presentation/api/v1/`
- **PDF Generator:** `loadtester/infrastructure/external/pdf_generator_service.py`

### Fixtures Globales (conftest.py)
```python
@pytest.fixture
async def db_session():
    """SQLite async session en memoria"""

@pytest.fixture
def mock_ai_client():
    """Mock de AI client"""

@pytest.fixture
def degradation_settings():
    """Configuración de degradación"""
```

---

## ✅ Checklist para Mañana

### Pre-Inicio
- [ ] Activar venv: `source ../.venv/Scripts/activate`
- [ ] Verificar estado actual: `python -m pytest tests/integration/ -v`
- [ ] Confirmar 32/36 passing

### Correcciones
- [ ] Fix test_complete_scenario_generation_flow
- [ ] Fix test_scenario_generation_with_custom_data
- [ ] Fix test_scenario_mock_data_sufficient_count
- [ ] Fix test_scenario_data_uniqueness
- [ ] Verificar 36/36 passing

### Implementaciones
- [ ] Crear test_report_generation_flow.py
- [ ] Crear test_database_integration.py
- [ ] Crear test_api_endpoints.py
- [ ] Ejecutar cada archivo individualmente
- [ ] Corregir errores encontrados

### Validación Final
- [ ] Ejecutar suite completa
- [ ] Generar reporte de cobertura
- [ ] Verificar 70-85 tests passing
- [ ] Documentar resultados finales

---

## 📊 Métricas Actuales vs Objetivo

| Métrica | Actual | Objetivo | Progreso |
|---------|--------|----------|----------|
| Archivos | 3/6 | 6/6 | 50% |
| Tests | 36 | 70-85 | 42-51% |
| Passing | 32 | 70-85 | 38-46% |
| Pass Rate | 88.9% | 100% | 88.9% |

---

## 🚀 Motivación

**Ya hemos logrado:**
- ✅ 193 tests unitarios (100% passing)
- ✅ 32 tests de integración (funcionando)
- ✅ Infraestructura de testing robusta
- ✅ Flujos críticos validados (OpenAPI, Jobs)

**Mañana completaremos:**
- 🎯 100% de la estrategia de FASE 3
- 🎯 ~270-280 tests totales en el proyecto
- 🎯 Cobertura completa de flujos end-to-end
- 🎯 Proyecto con testing profesional de producción

---

**Creado:** 2025-01-08
**Para continuar:** 2025-01-09
**Tiempo estimado mañana:** 2-3 horas
**Dificultad:** Media (infraestructura ya está lista)

¡Todo listo para completar FASE 3 al 100% mañana! 🚀
