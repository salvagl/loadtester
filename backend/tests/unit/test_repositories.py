"""
Unit tests for Repository implementations
Tests CRUD operations for all repositories using SQLite in-memory database
"""

import pytest
from datetime import datetime
from loadtester.infrastructure.repositories.api_repository import APIRepository
from loadtester.infrastructure.repositories.endpoint_repository import EndpointRepository
from loadtester.infrastructure.repositories.test_scenario_repository import TestScenarioRepository
from loadtester.infrastructure.repositories.job_repository import JobRepository
from loadtester.infrastructure.repositories.test_execution_repository import TestExecutionRepository
from loadtester.infrastructure.repositories.test_result_repository import TestResultRepository
from tests.fixtures.mock_data import (
    create_mock_api,
    create_mock_endpoint,
    create_mock_test_scenario,
    create_mock_job,
    create_mock_test_execution,
    create_mock_test_result
)


# ============================================================================
# API REPOSITORY TESTS
# ============================================================================

@pytest.mark.unit
@pytest.mark.asyncio
@pytest.mark.requires_db
async def test_api_repository_create(db_session):
    """Test creating an API."""
    repo = APIRepository(db_session)
    api = create_mock_api(api_name="Test API", base_url="https://test.com")

    created_api = await repo.create(api)

    assert created_api.api_id is not None
    assert created_api.api_name == "Test API"
    assert created_api.base_url == "https://test.com"


@pytest.mark.unit
@pytest.mark.asyncio
@pytest.mark.requires_db
async def test_api_repository_get_by_id(db_session):
    """Test getting API by ID."""
    repo = APIRepository(db_session)
    api = create_mock_api()
    created_api = await repo.create(api)

    retrieved_api = await repo.get_by_id(created_api.api_id)

    assert retrieved_api is not None
    assert retrieved_api.api_id == created_api.api_id
    assert retrieved_api.api_name == created_api.api_name


@pytest.mark.unit
@pytest.mark.asyncio
@pytest.mark.requires_db
async def test_api_repository_get_by_id_not_found(db_session):
    """Test getting non-existent API returns None."""
    repo = APIRepository(db_session)

    retrieved_api = await repo.get_by_id(99999)

    assert retrieved_api is None


@pytest.mark.unit
@pytest.mark.asyncio
@pytest.mark.requires_db
async def test_api_repository_get_by_name(db_session):
    """Test getting API by name."""
    repo = APIRepository(db_session)
    api = create_mock_api(api_name="Unique API Name")
    await repo.create(api)

    retrieved_api = await repo.get_by_name("Unique API Name")

    assert retrieved_api is not None
    assert retrieved_api.api_name == "Unique API Name"


@pytest.mark.unit
@pytest.mark.asyncio
@pytest.mark.requires_db
async def test_api_repository_get_all(db_session):
    """Test getting all APIs."""
    repo = APIRepository(db_session)

    # Create multiple APIs
    await repo.create(create_mock_api(api_name="API 1"))
    await repo.create(create_mock_api(api_name="API 2"))
    await repo.create(create_mock_api(api_name="API 3"))

    all_apis = await repo.get_all()

    assert len(all_apis) >= 3
    api_names = {api.api_name for api in all_apis}
    assert "API 1" in api_names
    assert "API 2" in api_names
    assert "API 3" in api_names


@pytest.mark.unit
@pytest.mark.asyncio
@pytest.mark.requires_db
async def test_api_repository_update(db_session):
    """Test updating an API."""
    repo = APIRepository(db_session)
    api = create_mock_api(api_name="Original Name")
    created_api = await repo.create(api)

    # Update the API
    created_api.api_name = "Updated Name"
    created_api.base_url = "https://updated.com"
    updated_api = await repo.update(created_api)

    assert updated_api.api_name == "Updated Name"
    assert updated_api.base_url == "https://updated.com"


@pytest.mark.unit
@pytest.mark.asyncio
@pytest.mark.requires_db
async def test_api_repository_delete(db_session):
    """Test deleting an API (soft delete)."""
    repo = APIRepository(db_session)
    api = create_mock_api()
    created_api = await repo.create(api)

    # Delete the API
    result = await repo.delete(created_api.api_id)

    assert result is True

    # Should not appear in get_all (only active)
    all_apis = await repo.get_all()
    api_ids = {api.api_id for api in all_apis}
    assert created_api.api_id not in api_ids


# ============================================================================
# ENDPOINT REPOSITORY TESTS
# ============================================================================

@pytest.mark.unit
@pytest.mark.asyncio
@pytest.mark.requires_db
async def test_endpoint_repository_create(db_session):
    """Test creating an endpoint."""
    # First create an API
    api_repo = APIRepository(db_session)
    api = await api_repo.create(create_mock_api())

    # Create endpoint
    endpoint_repo = EndpointRepository(db_session)
    endpoint = create_mock_endpoint(api_id=api.api_id)
    created_endpoint = await endpoint_repo.create(endpoint)

    assert created_endpoint.endpoint_id is not None
    assert created_endpoint.api_id == api.api_id


@pytest.mark.unit
@pytest.mark.asyncio
@pytest.mark.requires_db
async def test_endpoint_repository_get_by_id(db_session):
    """Test getting endpoint by ID."""
    api_repo = APIRepository(db_session)
    api = await api_repo.create(create_mock_api())

    endpoint_repo = EndpointRepository(db_session)
    endpoint = await endpoint_repo.create(create_mock_endpoint(api_id=api.api_id))

    retrieved = await endpoint_repo.get_by_id(endpoint.endpoint_id)

    assert retrieved is not None
    assert retrieved.endpoint_id == endpoint.endpoint_id


@pytest.mark.unit
@pytest.mark.asyncio
@pytest.mark.requires_db
async def test_endpoint_repository_get_by_api(db_session):
    """Test getting endpoints by API ID."""
    api_repo = APIRepository(db_session)
    api = await api_repo.create(create_mock_api())

    endpoint_repo = EndpointRepository(db_session)
    await endpoint_repo.create(create_mock_endpoint(api_id=api.api_id, endpoint_name="Endpoint 1"))
    await endpoint_repo.create(create_mock_endpoint(api_id=api.api_id, endpoint_name="Endpoint 2"))

    endpoints = await endpoint_repo.get_by_api_id(api.api_id)

    assert len(endpoints) == 2


# ============================================================================
# TEST SCENARIO REPOSITORY TESTS
# ============================================================================

@pytest.mark.unit
@pytest.mark.asyncio
@pytest.mark.requires_db
async def test_scenario_repository_create(db_session):
    """Test creating a test scenario."""
    # Setup: create API and endpoint
    api_repo = APIRepository(db_session)
    api = await api_repo.create(create_mock_api())
    endpoint_repo = EndpointRepository(db_session)
    endpoint = await endpoint_repo.create(create_mock_endpoint(api_id=api.api_id))

    # Create scenario
    scenario_repo = TestScenarioRepository(db_session)
    scenario = create_mock_test_scenario(endpoint_id=endpoint.endpoint_id)
    created_scenario = await scenario_repo.create(scenario)

    assert created_scenario.scenario_id is not None
    assert created_scenario.endpoint_id == endpoint.endpoint_id


@pytest.mark.unit
@pytest.mark.asyncio
@pytest.mark.requires_db
async def test_scenario_repository_get_by_id(db_session):
    """Test getting scenario by ID."""
    api_repo = APIRepository(db_session)
    api = await api_repo.create(create_mock_api())
    endpoint_repo = EndpointRepository(db_session)
    endpoint = await endpoint_repo.create(create_mock_endpoint(api_id=api.api_id))

    scenario_repo = TestScenarioRepository(db_session)
    scenario = await scenario_repo.create(create_mock_test_scenario(endpoint_id=endpoint.endpoint_id))

    retrieved = await scenario_repo.get_by_id(scenario.scenario_id)

    assert retrieved is not None
    assert retrieved.scenario_id == scenario.scenario_id


@pytest.mark.unit
@pytest.mark.asyncio
@pytest.mark.requires_db
async def test_scenario_repository_get_by_endpoint(db_session):
    """Test getting scenarios by endpoint ID."""
    api_repo = APIRepository(db_session)
    api = await api_repo.create(create_mock_api())
    endpoint_repo = EndpointRepository(db_session)
    endpoint = await endpoint_repo.create(create_mock_endpoint(api_id=api.api_id))

    scenario_repo = TestScenarioRepository(db_session)
    await scenario_repo.create(create_mock_test_scenario(endpoint_id=endpoint.endpoint_id, scenario_name="Scenario 1"))
    await scenario_repo.create(create_mock_test_scenario(endpoint_id=endpoint.endpoint_id, scenario_name="Scenario 2"))

    scenarios = await scenario_repo.get_by_endpoint_id(endpoint.endpoint_id)

    assert len(scenarios) == 2


# ============================================================================
# JOB REPOSITORY TESTS
# ============================================================================

@pytest.mark.unit
@pytest.mark.asyncio
@pytest.mark.requires_db
async def test_job_repository_create(db_session):
    """Test creating a job."""
    job_repo = JobRepository(db_session)
    job = create_mock_job(job_id="test-job-123")

    created_job = await job_repo.create(job)

    assert created_job.job_id == "test-job-123"


@pytest.mark.unit
@pytest.mark.asyncio
@pytest.mark.requires_db
async def test_job_repository_get_by_id(db_session):
    """Test getting job by ID."""
    job_repo = JobRepository(db_session)
    job = await job_repo.create(create_mock_job(job_id="test-job-456"))

    retrieved = await job_repo.get_by_id("test-job-456")

    assert retrieved is not None
    assert retrieved.job_id == "test-job-456"


@pytest.mark.unit
@pytest.mark.asyncio
@pytest.mark.requires_db
async def test_job_repository_get_running_jobs(db_session):
    """Test getting running jobs."""
    from loadtester.domain.entities.domain_entities import JobStatus

    job_repo = JobRepository(db_session)
    await job_repo.create(create_mock_job(job_id="running-1", status=JobStatus.RUNNING))
    await job_repo.create(create_mock_job(job_id="running-2", status=JobStatus.RUNNING))
    await job_repo.create(create_mock_job(job_id="finished-1", status=JobStatus.FINISHED))

    running_jobs = await job_repo.get_running_jobs()

    assert len(running_jobs) == 2
    job_ids = {job.job_id for job in running_jobs}
    assert "running-1" in job_ids
    assert "running-2" in job_ids
    assert "finished-1" not in job_ids


# ============================================================================
# TEST EXECUTION REPOSITORY TESTS
# ============================================================================

@pytest.mark.unit
@pytest.mark.asyncio
@pytest.mark.requires_db
async def test_execution_repository_create(db_session):
    """Test creating a test execution."""
    # Setup
    api_repo = APIRepository(db_session)
    api = await api_repo.create(create_mock_api())
    endpoint_repo = EndpointRepository(db_session)
    endpoint = await endpoint_repo.create(create_mock_endpoint(api_id=api.api_id))
    scenario_repo = TestScenarioRepository(db_session)
    scenario = await scenario_repo.create(create_mock_test_scenario(endpoint_id=endpoint.endpoint_id))

    # Create execution
    exec_repo = TestExecutionRepository(db_session)
    execution = create_mock_test_execution(scenario_id=scenario.scenario_id)
    created_execution = await exec_repo.create(execution)

    assert created_execution.execution_id is not None
    assert created_execution.scenario_id == scenario.scenario_id


@pytest.mark.unit
@pytest.mark.asyncio
@pytest.mark.requires_db
async def test_execution_repository_get_by_id(db_session):
    """Test getting execution by ID."""
    api_repo = APIRepository(db_session)
    api = await api_repo.create(create_mock_api())
    endpoint_repo = EndpointRepository(db_session)
    endpoint = await endpoint_repo.create(create_mock_endpoint(api_id=api.api_id))
    scenario_repo = TestScenarioRepository(db_session)
    scenario = await scenario_repo.create(create_mock_test_scenario(endpoint_id=endpoint.endpoint_id))

    exec_repo = TestExecutionRepository(db_session)
    execution = await exec_repo.create(create_mock_test_execution(scenario_id=scenario.scenario_id))

    retrieved = await exec_repo.get_by_id(execution.execution_id)

    assert retrieved is not None
    assert retrieved.execution_id == execution.execution_id


# ============================================================================
# TEST RESULT REPOSITORY TESTS
# ============================================================================

@pytest.mark.unit
@pytest.mark.asyncio
@pytest.mark.requires_db
async def test_result_repository_create(db_session):
    """Test creating a test result."""
    # Setup
    api_repo = APIRepository(db_session)
    api = await api_repo.create(create_mock_api())
    endpoint_repo = EndpointRepository(db_session)
    endpoint = await endpoint_repo.create(create_mock_endpoint(api_id=api.api_id))
    scenario_repo = TestScenarioRepository(db_session)
    scenario = await scenario_repo.create(create_mock_test_scenario(endpoint_id=endpoint.endpoint_id))
    exec_repo = TestExecutionRepository(db_session)
    execution = await exec_repo.create(create_mock_test_execution(scenario_id=scenario.scenario_id))

    # Create result
    result_repo = TestResultRepository(db_session)
    result = create_mock_test_result(execution_id=execution.execution_id)
    created_result = await result_repo.create(result)

    assert created_result.result_id is not None
    assert created_result.execution_id == execution.execution_id


@pytest.mark.unit
@pytest.mark.asyncio
@pytest.mark.requires_db
async def test_result_repository_get_by_id(db_session):
    """Test getting result by ID."""
    api_repo = APIRepository(db_session)
    api = await api_repo.create(create_mock_api())
    endpoint_repo = EndpointRepository(db_session)
    endpoint = await endpoint_repo.create(create_mock_endpoint(api_id=api.api_id))
    scenario_repo = TestScenarioRepository(db_session)
    scenario = await scenario_repo.create(create_mock_test_scenario(endpoint_id=endpoint.endpoint_id))
    exec_repo = TestExecutionRepository(db_session)
    execution = await exec_repo.create(create_mock_test_execution(scenario_id=scenario.scenario_id))

    result_repo = TestResultRepository(db_session)
    result = await result_repo.create(create_mock_test_result(execution_id=execution.execution_id))

    retrieved = await result_repo.get_by_id(result.result_id)

    assert retrieved is not None
    assert retrieved.result_id == result.result_id


@pytest.mark.unit
@pytest.mark.asyncio
@pytest.mark.requires_db
async def test_result_repository_get_by_execution(db_session):
    """Test getting result by execution ID."""
    api_repo = APIRepository(db_session)
    api = await api_repo.create(create_mock_api())
    endpoint_repo = EndpointRepository(db_session)
    endpoint = await endpoint_repo.create(create_mock_endpoint(api_id=api.api_id))
    scenario_repo = TestScenarioRepository(db_session)
    scenario = await scenario_repo.create(create_mock_test_scenario(endpoint_id=endpoint.endpoint_id))
    exec_repo = TestExecutionRepository(db_session)
    execution = await exec_repo.create(create_mock_test_execution(scenario_id=scenario.scenario_id))

    result_repo = TestResultRepository(db_session)
    await result_repo.create(create_mock_test_result(execution_id=execution.execution_id))

    retrieved = await result_repo.get_by_execution_id(execution.execution_id)

    assert retrieved is not None
    assert retrieved.execution_id == execution.execution_id
