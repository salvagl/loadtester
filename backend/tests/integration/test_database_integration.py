"""
Integration tests for Database Integration
Tests relationships, cascades, transactions, and complex queries
"""

import pytest
from sqlalchemy.exc import IntegrityError
from loadtester.domain.entities.domain_entities import (
    API, Endpoint, TestScenario, TestExecution, ExecutionStatus, TestResult, Job, JobStatus
)
from loadtester.infrastructure.repositories.api_repository import APIRepository
from loadtester.infrastructure.repositories.endpoint_repository import EndpointRepository
from loadtester.infrastructure.repositories.test_scenario_repository import TestScenarioRepository
from loadtester.infrastructure.repositories.test_execution_repository import TestExecutionRepository
from loadtester.infrastructure.repositories.test_result_repository import TestResultRepository
from loadtester.infrastructure.repositories.job_repository import JobRepository
from tests.fixtures.mock_data import (
    create_mock_api, create_mock_endpoint, create_mock_test_scenario,
    create_mock_test_execution, create_mock_test_result, create_mock_job
)
from datetime import datetime


# ============================================================================
# INTEGRATION TEST: Database Relationships
# ============================================================================

@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.requires_db
async def test_api_endpoint_relationship(db_session):
    """Test that API has multiple Endpoints relationship."""
    api_repo = APIRepository(db_session)
    endpoint_repo = EndpointRepository(db_session)

    # Create API
    api = create_mock_api(api_name="Relationship Test API")
    created_api = await api_repo.create(api)

    # Create 3 endpoints for this API
    endpoints = []
    for i in range(3):
        endpoint = create_mock_endpoint(
            api_id=created_api.api_id,
            endpoint_path=f"/endpoint{i}"
        )
        created_endpoint = await endpoint_repo.create(endpoint)
        endpoints.append(created_endpoint)

    # Verify relationship
    retrieved_endpoints = await endpoint_repo.get_by_api_id(created_api.api_id)
    assert len(retrieved_endpoints) == 3
    assert all(ep.api_id == created_api.api_id for ep in retrieved_endpoints)


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.requires_db
async def test_endpoint_scenario_relationship(db_session):
    """Test that Endpoint has multiple Scenarios relationship."""
    api_repo = APIRepository(db_session)
    endpoint_repo = EndpointRepository(db_session)
    scenario_repo = TestScenarioRepository(db_session)

    # Create API and Endpoint
    api = create_mock_api()
    created_api = await api_repo.create(api)

    endpoint = create_mock_endpoint(api_id=created_api.api_id)
    created_endpoint = await endpoint_repo.create(endpoint)

    # Create 4 scenarios for this endpoint
    scenarios = []
    for i in range(4):
        scenario = create_mock_test_scenario(
            endpoint_id=created_endpoint.endpoint_id,
            scenario_name=f"Scenario {i+1}"
        )
        created_scenario = await scenario_repo.create(scenario)
        scenarios.append(created_scenario)

    # Verify relationship
    retrieved_scenarios = await scenario_repo.get_by_endpoint_id(created_endpoint.endpoint_id)
    assert len(retrieved_scenarios) == 4
    assert all(s.endpoint_id == created_endpoint.endpoint_id for s in retrieved_scenarios)


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.requires_db
async def test_scenario_execution_relationship(db_session):
    """Test that Scenario has multiple Executions relationship."""
    scenario_repo = TestScenarioRepository(db_session)
    execution_repo = TestExecutionRepository(db_session)

    # Create scenario
    scenario = create_mock_test_scenario()
    created_scenario = await scenario_repo.create(scenario)

    # Create 2 executions for this scenario
    executions = []
    for i in range(2):
        execution = TestExecution(
            scenario_id=created_scenario.scenario_id,
            execution_name=f"Execution {i+1}",
            status=ExecutionStatus.PENDING,
            start_time=datetime.utcnow()
        )
        created_execution = await execution_repo.create(execution)
        executions.append(created_execution)

    # Verify relationship
    retrieved_executions = await execution_repo.get_by_scenario_id(created_scenario.scenario_id)
    assert len(retrieved_executions) == 2
    assert all(e.scenario_id == created_scenario.scenario_id for e in retrieved_executions)


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.requires_db
async def test_execution_result_relationship(db_session):
    """Test that Execution has one Result relationship."""
    execution_repo = TestExecutionRepository(db_session)
    result_repo = TestResultRepository(db_session)

    # Create execution
    execution = create_mock_test_execution()
    created_execution = await execution_repo.create(execution)

    # Create result for this execution
    result = create_mock_test_result(execution_id=created_execution.execution_id)
    created_result = await result_repo.create(result)

    # Verify relationship
    retrieved_result = await result_repo.get_by_execution_id(created_execution.execution_id)
    assert retrieved_result is not None
    assert retrieved_result.execution_id == created_execution.execution_id


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.requires_db
async def test_complete_relationship_chain(db_session):
    """Test complete chain: API → Endpoint → Scenario → Execution → Result."""
    # Initialize all repositories
    api_repo = APIRepository(db_session)
    endpoint_repo = EndpointRepository(db_session)
    scenario_repo = TestScenarioRepository(db_session)
    execution_repo = TestExecutionRepository(db_session)
    result_repo = TestResultRepository(db_session)

    # Create complete chain
    api = create_mock_api(api_name="Chain Test API")
    created_api = await api_repo.create(api)

    endpoint = create_mock_endpoint(api_id=created_api.api_id)
    created_endpoint = await endpoint_repo.create(endpoint)

    scenario = create_mock_test_scenario(endpoint_id=created_endpoint.endpoint_id)
    created_scenario = await scenario_repo.create(scenario)

    execution = TestExecution(
        scenario_id=created_scenario.scenario_id,
        execution_name="Chain Test Execution",
        status=ExecutionStatus.FINISHED,
        start_time=datetime.utcnow(),
        end_time=datetime.utcnow()
    )
    created_execution = await execution_repo.create(execution)

    result = create_mock_test_result(execution_id=created_execution.execution_id)
    created_result = await result_repo.create(result)

    # Verify entire chain
    assert created_result.execution_id == created_execution.execution_id
    assert created_execution.scenario_id == created_scenario.scenario_id
    assert created_scenario.endpoint_id == created_endpoint.endpoint_id
    assert created_endpoint.api_id == created_api.api_id


# ============================================================================
# INTEGRATION TEST: Cascades and Deletes
# ============================================================================

@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.requires_db
async def test_delete_api_removes_reference(db_session):
    """Test deleting an API (endpoints may remain or be handled by cascade)."""
    api_repo = APIRepository(db_session)
    endpoint_repo = EndpointRepository(db_session)

    # Create API with endpoint
    api = create_mock_api()
    created_api = await api_repo.create(api)

    endpoint = create_mock_endpoint(api_id=created_api.api_id)
    created_endpoint = await endpoint_repo.create(endpoint)

    # Delete API (soft delete - marks active=False)
    await api_repo.delete(created_api.api_id)

    # Verify API is soft deleted (active=False)
    deleted_api = await api_repo.get_by_id(created_api.api_id)
    assert deleted_api is not None
    assert deleted_api.active is False


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.requires_db
async def test_delete_endpoint(db_session):
    """Test deleting an endpoint."""
    api_repo = APIRepository(db_session)
    endpoint_repo = EndpointRepository(db_session)

    # Create API and endpoint
    api = create_mock_api()
    created_api = await api_repo.create(api)

    endpoint = create_mock_endpoint(api_id=created_api.api_id)
    created_endpoint = await endpoint_repo.create(endpoint)

    # Delete endpoint (soft delete - marks active=False)
    await endpoint_repo.delete(created_endpoint.endpoint_id)

    # Verify endpoint is soft deleted (active=False) but API remains active
    deleted_endpoint = await endpoint_repo.get_by_id(created_endpoint.endpoint_id)
    assert deleted_endpoint is not None
    assert deleted_endpoint.active is False

    api_still_exists = await api_repo.get_by_id(created_api.api_id)
    assert api_still_exists is not None
    assert api_still_exists.active is True


# ============================================================================
# INTEGRATION TEST: Queries
# ============================================================================

@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.requires_db
async def test_get_running_jobs_query(db_session):
    """Test querying running jobs."""
    job_repo = JobRepository(db_session)

    # Create jobs with different statuses
    from uuid import uuid4
    pending_job = Job(
        job_id=str(uuid4()),
        job_type="load_test",
        status=JobStatus.PENDING,
        created_at=datetime.utcnow()
    )
    await job_repo.create(pending_job)

    running_job1 = Job(
        job_id=str(uuid4()),
        job_type="load_test",
        status=JobStatus.RUNNING,
        created_at=datetime.utcnow()
    )
    await job_repo.create(running_job1)

    running_job2 = Job(
        job_id=str(uuid4()),
        job_type="load_test",
        status=JobStatus.RUNNING,
        created_at=datetime.utcnow()
    )
    await job_repo.create(running_job2)

    finished_job = Job(
        job_id=str(uuid4()),
        job_type="load_test",
        status=JobStatus.FINISHED,
        created_at=datetime.utcnow()
    )
    await job_repo.create(finished_job)

    # Query running jobs
    running_jobs = await job_repo.get_running_jobs()

    # Should only return RUNNING jobs
    assert len(running_jobs) >= 2
    running_job_ids = [j.job_id for j in running_jobs]
    assert running_job1.job_id in running_job_ids
    assert running_job2.job_id in running_job_ids
    assert all(j.status == JobStatus.RUNNING for j in running_jobs)


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.requires_db
async def test_get_scenarios_by_endpoint(db_session):
    """Test querying scenarios by endpoint."""
    api_repo = APIRepository(db_session)
    endpoint_repo = EndpointRepository(db_session)
    scenario_repo = TestScenarioRepository(db_session)

    # Create API and 2 endpoints
    api = create_mock_api()
    created_api = await api_repo.create(api)

    endpoint1 = create_mock_endpoint(api_id=created_api.api_id, endpoint_path="/endpoint1")
    endpoint2 = create_mock_endpoint(api_id=created_api.api_id, endpoint_path="/endpoint2")
    created_endpoint1 = await endpoint_repo.create(endpoint1)
    created_endpoint2 = await endpoint_repo.create(endpoint2)

    # Create scenarios for endpoint1
    for i in range(3):
        scenario = create_mock_test_scenario(
            endpoint_id=created_endpoint1.endpoint_id,
            scenario_name=f"E1 Scenario {i}"
        )
        await scenario_repo.create(scenario)

    # Create scenarios for endpoint2
    for i in range(2):
        scenario = create_mock_test_scenario(
            endpoint_id=created_endpoint2.endpoint_id,
            scenario_name=f"E2 Scenario {i}"
        )
        await scenario_repo.create(scenario)

    # Query scenarios by endpoint
    endpoint1_scenarios = await scenario_repo.get_by_endpoint_id(created_endpoint1.endpoint_id)
    endpoint2_scenarios = await scenario_repo.get_by_endpoint_id(created_endpoint2.endpoint_id)

    assert len(endpoint1_scenarios) == 3
    assert len(endpoint2_scenarios) == 2


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.requires_db
async def test_get_endpoints_by_api(db_session):
    """Test querying endpoints by API."""
    api_repo = APIRepository(db_session)
    endpoint_repo = EndpointRepository(db_session)

    # Create 2 APIs
    api1 = create_mock_api(api_name="API 1")
    api2 = create_mock_api(api_name="API 2")
    created_api1 = await api_repo.create(api1)
    created_api2 = await api_repo.create(api2)

    # Create endpoints for api1
    for i in range(4):
        endpoint = create_mock_endpoint(
            api_id=created_api1.api_id,
            endpoint_path=f"/api1/endpoint{i}"
        )
        await endpoint_repo.create(endpoint)

    # Create endpoints for api2
    for i in range(2):
        endpoint = create_mock_endpoint(
            api_id=created_api2.api_id,
            endpoint_path=f"/api2/endpoint{i}"
        )
        await endpoint_repo.create(endpoint)

    # Query endpoints by API
    api1_endpoints = await endpoint_repo.get_by_api_id(created_api1.api_id)
    api2_endpoints = await endpoint_repo.get_by_api_id(created_api2.api_id)

    assert len(api1_endpoints) == 4
    assert len(api2_endpoints) == 2


# ============================================================================
# INTEGRATION TEST: Uniqueness and Constraints
# ============================================================================

@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.requires_db
async def test_unique_job_id_constraint(db_session):
    """Test that job_id must be unique."""
    job_repo = JobRepository(db_session)

    job_id = "unique-test-job-123"

    # Create first job
    job1 = Job(
        job_id=job_id,
        job_type="load_test",
        status=JobStatus.PENDING,
        created_at=datetime.utcnow()
    )
    await job_repo.create(job1)

    # Try to create second job with same ID (should fail)
    job2 = Job(
        job_id=job_id,
        job_type="load_test",
        status=JobStatus.PENDING,
        created_at=datetime.utcnow()
    )

    with pytest.raises(Exception):  # Should raise IntegrityError or similar
        await job_repo.create(job2)


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.requires_db
async def test_multiple_apis_different_names(db_session):
    """Test creating multiple APIs with different names."""
    api_repo = APIRepository(db_session)

    # Create 5 APIs with different names
    apis = []
    for i in range(5):
        api = create_mock_api(api_name=f"API {i}")
        created_api = await api_repo.create(api)
        apis.append(created_api)

    # Verify all were created
    assert len(apis) == 5
    assert len(set(api.api_id for api in apis)) == 5  # All different IDs
