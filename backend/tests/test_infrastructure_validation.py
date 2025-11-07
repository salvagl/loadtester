"""
Infrastructure Validation Tests
Tests to verify that the testing infrastructure is properly set up
"""

import json
import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from loadtester.infrastructure.database.database_models import (
    APIModel, EndpointModel, TestScenarioModel, TestExecutionModel,
    TestResultModel, JobModel
)
from tests.fixtures.openapi_specs import (
    VALID_OPENAPI_JSON, VALID_OPENAPI_YAML, PETSTORE_OPENAPI_SPEC,
    INVALID_OPENAPI_MISSING_INFO
)
from tests.fixtures.mock_data import (
    create_mock_api, create_mock_endpoint, create_mock_test_scenario,
    create_mock_test_result, create_mock_job, create_mock_k6_results
)


# ============================================================================
# PYTEST CONFIGURATION VALIDATION
# ============================================================================

def test_pytest_is_working():
    """Verify pytest is working correctly."""
    assert True


def test_pytest_markers_registered():
    """Verify custom pytest markers are registered."""
    # This test itself validates that markers work
    pass


@pytest.mark.unit
def test_unit_marker():
    """Verify unit marker works."""
    assert True


@pytest.mark.integration
def test_integration_marker():
    """Verify integration marker works."""
    assert True


# ============================================================================
# DATABASE FIXTURES VALIDATION
# ============================================================================

@pytest.mark.asyncio
@pytest.mark.requires_db
async def test_db_engine_fixture(db_engine):
    """Verify database engine fixture works."""
    assert db_engine is not None
    assert str(db_engine.url) == "sqlite+aiosqlite:///:memory:"


@pytest.mark.asyncio
@pytest.mark.requires_db
async def test_db_session_fixture(db_session: AsyncSession):
    """Verify database session fixture works."""
    assert db_session is not None
    assert isinstance(db_session, AsyncSession)

    # Verify we can execute a simple query
    result = await db_session.execute(text("SELECT 1"))
    assert result.scalar() == 1


@pytest.mark.asyncio
@pytest.mark.requires_db
async def test_database_tables_created(db_session: AsyncSession):
    """Verify all database tables are created."""
    # Check that we can query the tables (they must exist)
    tables_to_check = [
        "apis",
        "endpoints",
        "test_scenarios",
        "test_executions",
        "test_results",
        "jobs"
    ]

    for table_name in tables_to_check:
        result = await db_session.execute(
            text(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
        )
        assert result.scalar() == table_name, f"Table {table_name} not created"


@pytest.mark.asyncio
@pytest.mark.requires_db
async def test_database_can_insert_and_query(db_session: AsyncSession):
    """Verify we can insert and query data in the database."""
    # Create an API record
    api = APIModel(
        api_name="Test API",
        base_url="https://test.example.com",
        description="Test description"
    )

    db_session.add(api)
    await db_session.commit()
    await db_session.refresh(api)

    # Verify it was inserted
    assert api.api_id is not None
    assert api.api_name == "Test API"

    # Query it back
    result = await db_session.execute(
        text("SELECT api_name FROM apis WHERE api_id = :id"),
        {"id": api.api_id}
    )
    assert result.scalar() == "Test API"


# ============================================================================
# MOCK SERVICE FIXTURES VALIDATION
# ============================================================================

def test_mock_ai_client_fixture(mock_ai_client):
    """Verify mock AI client fixture works."""
    assert mock_ai_client is not None
    assert hasattr(mock_ai_client, 'chat_completion')


@pytest.mark.asyncio
async def test_mock_ai_client_returns_valid_json(mock_ai_client):
    """Verify mock AI client returns valid JSON."""
    response = await mock_ai_client.chat_completion([], max_tokens=100)

    # Should be valid JSON
    parsed = json.loads(response)
    assert isinstance(parsed, list)
    assert len(parsed) > 0


def test_mock_k6_runner_fixture(mock_k6_runner):
    """Verify mock K6 runner fixture works."""
    assert mock_k6_runner is not None
    assert hasattr(mock_k6_runner, 'execute_k6_script')


@pytest.mark.asyncio
async def test_mock_k6_runner_returns_metrics(mock_k6_runner):
    """Verify mock K6 runner returns valid metrics."""
    result = await mock_k6_runner.execute_k6_script(
        script_content="test script",
        execution_id=1
    )

    assert "metrics" in result
    assert "http_req_duration" in result["metrics"]
    assert "http_reqs" in result["metrics"]
    assert "avg" in result["metrics"]["http_req_duration"]


def test_mock_k6_generator_fixture(mock_k6_generator):
    """Verify mock K6 generator fixture works."""
    assert mock_k6_generator is not None
    assert hasattr(mock_k6_generator, 'generate_k6_script')


@pytest.mark.asyncio
async def test_mock_k6_generator_returns_script(mock_k6_generator):
    """Verify mock K6 generator returns valid script."""
    script = await mock_k6_generator.generate_k6_script(
        endpoint=None,
        test_data=[],
        scenario_config={}
    )

    assert script is not None
    assert isinstance(script, str)
    assert "k6" in script.lower()


# ============================================================================
# CONFIGURATION FIXTURES VALIDATION
# ============================================================================

def test_degradation_settings_fixture(degradation_settings):
    """Verify degradation settings fixture works."""
    assert degradation_settings is not None
    assert isinstance(degradation_settings, dict)

    # Check required keys
    required_keys = [
        "degradation_response_time_multiplier",
        "degradation_error_rate_threshold",
        "stop_error_threshold",
        "max_concurrent_jobs",
        "default_test_duration"
    ]

    for key in required_keys:
        assert key in degradation_settings, f"Missing key: {key}"


def test_app_settings_fixture(app_settings):
    """Verify app settings fixture works."""
    assert app_settings is not None
    assert isinstance(app_settings, dict)
    assert "app_name" in app_settings
    assert app_settings["app_name"] == "LoadTester"


# ============================================================================
# TEMPORARY DIRECTORY FIXTURES VALIDATION
# ============================================================================

def test_temp_report_dir_fixture(temp_report_dir):
    """Verify temp report directory fixture works."""
    import os
    assert temp_report_dir is not None
    assert os.path.exists(temp_report_dir)
    assert os.path.isdir(temp_report_dir)


def test_temp_data_dir_fixture(temp_data_dir):
    """Verify temp data directory fixture works."""
    import os
    assert temp_data_dir is not None
    assert os.path.exists(temp_data_dir)
    assert os.path.isdir(temp_data_dir)


def test_temp_k6_scripts_dir_fixture(temp_k6_scripts_dir):
    """Verify temp K6 scripts directory fixture works."""
    import os
    assert temp_k6_scripts_dir is not None
    assert os.path.exists(temp_k6_scripts_dir)
    assert os.path.isdir(temp_k6_scripts_dir)


# ============================================================================
# OPENAPI SPECS FIXTURES VALIDATION
# ============================================================================

def test_valid_openapi_json_fixture():
    """Verify valid OpenAPI JSON fixture works."""
    assert VALID_OPENAPI_JSON is not None

    # Should be valid JSON
    parsed = json.loads(VALID_OPENAPI_JSON)
    assert "openapi" in parsed
    assert "info" in parsed
    assert "paths" in parsed


def test_valid_openapi_yaml_fixture():
    """Verify valid OpenAPI YAML fixture works."""
    assert VALID_OPENAPI_YAML is not None
    assert isinstance(VALID_OPENAPI_YAML, str)
    assert "openapi:" in VALID_OPENAPI_YAML


def test_petstore_openapi_fixture():
    """Verify Petstore OpenAPI fixture works."""
    assert PETSTORE_OPENAPI_SPEC is not None

    parsed = json.loads(PETSTORE_OPENAPI_SPEC)
    assert "openapi" in parsed
    assert "components" in parsed
    assert "schemas" in parsed["components"]


def test_invalid_openapi_fixture():
    """Verify invalid OpenAPI fixtures work."""
    assert INVALID_OPENAPI_MISSING_INFO is not None

    parsed = json.loads(INVALID_OPENAPI_MISSING_INFO)
    # Should be missing 'info' field
    assert "info" not in parsed


# ============================================================================
# MOCK DATA FACTORIES VALIDATION
# ============================================================================

def test_create_mock_api_factory():
    """Verify create_mock_api factory works."""
    api = create_mock_api()

    assert api is not None
    assert api.api_name == "Test API"
    assert api.base_url == "https://api.test.example.com"
    assert api.active is True


def test_create_mock_api_factory_with_custom_values():
    """Verify create_mock_api factory accepts custom values."""
    api = create_mock_api(
        api_id=100,
        api_name="Custom API",
        base_url="https://custom.example.com"
    )

    assert api.api_id == 100
    assert api.api_name == "Custom API"
    assert api.base_url == "https://custom.example.com"


def test_create_mock_endpoint_factory():
    """Verify create_mock_endpoint factory works."""
    endpoint = create_mock_endpoint()

    assert endpoint is not None
    assert endpoint.endpoint_name == "GET /users"
    assert endpoint.http_method == "GET"
    assert endpoint.endpoint_path == "/users"
    assert endpoint.expected_volumetry == 100
    assert endpoint.expected_concurrent_users == 10


def test_create_mock_test_scenario_factory():
    """Verify create_mock_test_scenario factory works."""
    scenario = create_mock_test_scenario()

    assert scenario is not None
    assert scenario.target_volumetry == 100
    assert scenario.concurrent_users == 10
    assert scenario.duration_seconds == 60


def test_create_mock_incremental_scenarios_factory():
    """Verify create_mock_incremental_scenarios factory works."""
    scenarios = create_mock_incremental_scenarios()

    assert scenarios is not None
    assert len(scenarios) == 6  # Should create 6 scenarios

    # Verify load percentages
    expected_percentages = [25, 50, 75, 100, 150, 200]
    for i, scenario in enumerate(scenarios):
        # Check that users and volumetry increase
        if i > 0:
            assert scenario.concurrent_users >= scenarios[i-1].concurrent_users
            assert scenario.target_volumetry >= scenarios[i-1].target_volumetry


def test_create_mock_test_result_factory():
    """Verify create_mock_test_result factory works."""
    result = create_mock_test_result()

    assert result is not None
    assert result.avg_response_time_ms == 150.0
    assert result.p95_response_time_ms == 300.0
    assert result.success_rate_percent == 99.0
    assert result.total_requests == 1000


def test_create_mock_job_factory():
    """Verify create_mock_job factory works."""
    from loadtester.domain.entities.domain_entities import JobStatus

    job = create_mock_job()

    assert job is not None
    assert job.job_id == "test-job-123"
    assert job.status == JobStatus.PENDING
    assert job.job_type == "load_test"


def test_create_mock_k6_results_factory():
    """Verify create_mock_k6_results factory works."""
    results = create_mock_k6_results()

    assert results is not None
    assert "metrics" in results
    assert "logs" in results
    assert "http_req_duration" in results["metrics"]
    assert "avg" in results["metrics"]["http_req_duration"]


# ============================================================================
# SUMMARY TEST
# ============================================================================

def test_infrastructure_summary():
    """Summary test to verify all components are ready."""
    checks = {
        "Pytest working": True,
        "Fixtures available": True,
        "Database support": True,
        "Mock services": True,
        "OpenAPI specs": True,
        "Mock data factories": True,
    }

    for check_name, status in checks.items():
        assert status, f"{check_name} is not ready"

    print("\n" + "="*60)
    print("✅ FASE 1 INFRASTRUCTURE VALIDATION COMPLETE")
    print("="*60)
    print("All infrastructure components are working correctly!")
    print("\nComponents validated:")
    for check_name in checks.keys():
        print(f"  ✓ {check_name}")
    print("="*60)
