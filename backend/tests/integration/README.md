# Integration Tests - Quick Reference

**Status**: ✅ COMPLETE (100% según estrategia original)
**Tests**: 83/83 passing (100%)
**Coverage**: 45% (integration focus)
**Execution Time**: ~2 minutes 15 seconds

---

## Test Files

### 1. [test_api_endpoints.py](test_api_endpoints.py) (23 tests) ✅
FastAPI REST endpoint integration tests
- OpenAPI validation (JSON/YAML)
- OpenAPI parsing and extraction
- Job status endpoints
- Request validation
- Service integration
- **NEW: POST /api/v1/load-test** (3 tests)
- **NEW: GET /api/v1/report/{job_id}** (3 tests)
- **NEW: GET /api/v1/health** (1 test)

### 2. [test_database_integration.py](test_database_integration.py) (12 tests)
Database relationships and queries
- Entity relationships (API→Endpoint→Scenario→Execution→Result)
- Soft delete operations
- Complex queries
- Uniqueness constraints

### 3. [test_job_execution_flow.py](test_job_execution_flow.py) (14 tests)
Job execution lifecycle
- Job status transitions
- Progress tracking
- Failure handling
- Concurrent execution
- Timeout and cancellation

### 4. [test_openapi_flow.py](test_openapi_flow.py) (11 tests)
OpenAPI specification workflows
- Complete parsing flow
- $ref resolution
- YAML support
- Large spec handling
- Authentication schemas

### 5. [test_report_generation_flow.py](test_report_generation_flow.py) (12 tests)
PDF report generation
- Complete report flow
- Performance classification
- Degradation detection
- Multiple results aggregation
- File validation

### 6. [test_scenario_flow.py](test_scenario_flow.py) (11 tests)
Test scenario generation
- Mock data generation
- Data uniqueness
- Load configuration (minimal/high)
- Duration and ramp settings
- Scenario updates

---

## Running Tests

### Run all integration tests
```bash
cd backend
source ../.venv/Scripts/activate  # Windows Git Bash
python -m pytest tests/integration/ -v
```

### Run specific test file
```bash
python -m pytest tests/integration/test_api_endpoints.py -v
```

### Run specific test
```bash
python -m pytest tests/integration/test_api_endpoints.py::test_validate_openapi_spec_valid_json -v
```

### Run with coverage
```bash
python -m pytest tests/integration/ --cov=loadtester --cov-report=html --cov-report=term
```

### Run tests by marker
```bash
# Integration tests only
python -m pytest tests/integration/ -m integration

# Database-dependent tests
python -m pytest tests/integration/ -m requires_db
```

---

## Test Markers

- `@pytest.mark.integration` - Integration test
- `@pytest.mark.asyncio` - Async test
- `@pytest.mark.requires_db` - Requires database

---

## Key Fixtures

### `db_session`
In-memory SQLite database session for each test
- Auto-created and destroyed
- Isolated per test
- Async support

### `mock_ai_client`
Mocked AI service client
- Returns sample data
- No external API calls

### `tmp_path`
Temporary directory for file operations
- Auto-cleaned after test
- Unique per test

---

## Coverage Report

View HTML coverage report:
```bash
cd backend
# Generate if not exists
python -m pytest tests/integration/ --cov=loadtester --cov-report=html

# Open in browser (Windows Git Bash)
start htmlcov/index.html
```

**Current Coverage**: 42%
- database_models.py: 100%
- dependency_container.py: 86%
- domain_entities.py: 83%
- openapi_endpoints.py: 66%
- pdf_generator_service.py: 64%

---

## Common Issues

### Issue 1: Database Locked
**Error**: `OperationalError: database is locked`
**Fix**: Use in-memory SQLite (`:memory:`) - already configured in conftest.py

### Issue 2: Async Test Failures
**Error**: `RuntimeError: Event loop is closed`
**Fix**: Add `@pytest.mark.asyncio` decorator

### Issue 3: Soft Delete Confusion
**Error**: `AssertionError: assert None is not None`
**Fix**: Repository delete() performs soft delete (sets `active=False`)
```python
# Correct way to test delete
deleted_api = await api_repo.get_by_id(api_id)
assert deleted_api.active is False  # Not: assert deleted_api is None
```

---

## Test Data Factories

Located in `tests/fixtures/mock_data.py`:
- `create_mock_api()` - Create API entity
- `create_mock_endpoint()` - Create Endpoint entity
- `create_mock_endpoint_post()` - Create POST endpoint
- `create_mock_test_scenario()` - Create TestScenario entity
- `create_mock_test_execution()` - Create TestExecution entity
- `create_mock_test_result()` - Create TestResult entity
- `create_mock_job()` - Create Job entity

---

## Documentation

- [Testing Strategy](../../docs/testing_strategy.md) - Complete testing documentation
- [FASE 3 Summary](../../docs/FASE3_COMPLETE_SUMMARY.md) - Detailed completion report
- [Quick Reference](../../docs/testing_quick_reference.md) - Quick testing guide

---

**Last Updated**: November 9, 2025
**Tests**: 83/83 passing (100%)
**Strategy Compliance**: 100% - All tests from original testing_strategy.md implemented
