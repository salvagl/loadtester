"""
Integration tests for API REST Endpoints
Tests FastAPI endpoints with TestClient
"""

import pytest
import json
from tests.fixtures.openapi_specs import VALID_OPENAPI_JSON, VALID_OPENAPI_YAML

# Note: Since we need FastAPI app instance and we don't have a clear main.py,
# these tests focus on the endpoint modules directly

# ============================================================================
# INTEGRATION TEST: OpenAPI Endpoints
# ============================================================================

@pytest.mark.integration
@pytest.mark.asyncio
async def test_validate_openapi_spec_valid_json(mock_ai_client):
    """Test validating a valid JSON OpenAPI spec."""
    from loadtester.presentation.api.v1.openapi_endpoints import validate_openapi_spec, OpenAPISpecRequest
    from loadtester.infrastructure.external.local_openapi_parser import LocalOpenAPIParser

    parser = LocalOpenAPIParser()
    request = OpenAPISpecRequest(spec_content=VALID_OPENAPI_JSON)

    response = await validate_openapi_spec(request, parser)

    assert response.valid is True
    assert response.message == "OpenAPI specification is valid"
    assert len(response.errors) == 0


@pytest.mark.integration
@pytest.mark.asyncio
async def test_validate_openapi_spec_valid_yaml(mock_ai_client):
    """Test validating a valid YAML OpenAPI spec."""
    from loadtester.presentation.api.v1.openapi_endpoints import validate_openapi_spec, OpenAPISpecRequest
    from loadtester.infrastructure.external.local_openapi_parser import LocalOpenAPIParser

    parser = LocalOpenAPIParser()
    request = OpenAPISpecRequest(spec_content=VALID_OPENAPI_YAML)

    response = await validate_openapi_spec(request, parser)

    assert response.valid is True


@pytest.mark.integration
@pytest.mark.asyncio
async def test_validate_openapi_spec_invalid():
    """Test validating an invalid OpenAPI spec."""
    from loadtester.presentation.api.v1.openapi_endpoints import validate_openapi_spec, OpenAPISpecRequest
    from loadtester.infrastructure.external.local_openapi_parser import LocalOpenAPIParser

    parser = LocalOpenAPIParser()
    invalid_spec = "This is not a valid OpenAPI spec"
    request = OpenAPISpecRequest(spec_content=invalid_spec)

    response = await validate_openapi_spec(request, parser)

    assert response.valid is False
    assert len(response.errors) > 0


@pytest.mark.integration
@pytest.mark.asyncio
async def test_parse_openapi_spec_success():
    """Test parsing a valid OpenAPI spec."""
    from loadtester.presentation.api.v1.openapi_endpoints import parse_openapi_spec, OpenAPISpecRequest
    from loadtester.infrastructure.external.local_openapi_parser import LocalOpenAPIParser

    parser = LocalOpenAPIParser()
    request = OpenAPISpecRequest(spec_content=VALID_OPENAPI_JSON)

    response = await parse_openapi_spec(request, parser)

    assert response.total_endpoints > 0
    assert len(response.endpoints) > 0
    assert "title" in response.info


@pytest.mark.integration
@pytest.mark.asyncio
async def test_parse_openapi_spec_invalid():
    """Test parsing an invalid OpenAPI spec."""
    from loadtester.presentation.api.v1.openapi_endpoints import parse_openapi_spec, OpenAPISpecRequest
    from loadtester.infrastructure.external.local_openapi_parser import LocalOpenAPIParser
    from fastapi import HTTPException

    parser = LocalOpenAPIParser()
    invalid_spec = "Not valid OpenAPI"
    request = OpenAPISpecRequest(spec_content=invalid_spec)

    with pytest.raises(HTTPException) as exc_info:
        await parse_openapi_spec(request, parser)

    assert exc_info.value.status_code == 400


# ============================================================================
# INTEGRATION TEST: Status Endpoints
# ============================================================================

@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.requires_db
async def test_get_job_status_pending(db_session):
    """Test getting status of a pending job."""
    from loadtester.infrastructure.repositories.job_repository import JobRepository
    from loadtester.domain.entities.domain_entities import Job, JobStatus
    from datetime import datetime
    from uuid import uuid4

    job_repo = JobRepository(db_session)

    # Create pending job
    job = Job(
        job_id=str(uuid4()),
        job_type="load_test",
        status=JobStatus.PENDING,
        created_at=datetime.utcnow()
    )
    created_job = await job_repo.create(job)

    # Get job status
    retrieved_job = await job_repo.get_by_id(created_job.job_id)

    assert retrieved_job is not None
    assert retrieved_job.status == JobStatus.PENDING
    assert retrieved_job.progress_percentage == 0.0


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.requires_db
async def test_get_job_status_running(db_session):
    """Test getting status of a running job."""
    from loadtester.infrastructure.repositories.job_repository import JobRepository
    from loadtester.domain.entities.domain_entities import Job, JobStatus
    from datetime import datetime
    from uuid import uuid4

    job_repo = JobRepository(db_session)

    # Create running job
    job = Job(
        job_id=str(uuid4()),
        job_type="load_test",
        status=JobStatus.RUNNING,
        progress_percentage=45.0,
        created_at=datetime.utcnow(),
        started_at=datetime.utcnow()
    )
    created_job = await job_repo.create(job)

    # Get job status
    retrieved_job = await job_repo.get_by_id(created_job.job_id)

    assert retrieved_job is not None
    assert retrieved_job.status == JobStatus.RUNNING
    assert retrieved_job.progress_percentage == 45.0


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.requires_db
async def test_get_job_status_finished(db_session):
    """Test getting status of a finished job."""
    from loadtester.infrastructure.repositories.job_repository import JobRepository
    from loadtester.domain.entities.domain_entities import Job, JobStatus
    from datetime import datetime
    from uuid import uuid4

    job_repo = JobRepository(db_session)

    # Create finished job
    job = Job(
        job_id=str(uuid4()),
        job_type="load_test",
        status=JobStatus.FINISHED,
        progress_percentage=100.0,
        created_at=datetime.utcnow(),
        started_at=datetime.utcnow(),
        finished_at=datetime.utcnow(),
        result_data={"report_path": "/reports/test.pdf"}
    )
    created_job = await job_repo.create(job)

    # Get job status
    retrieved_job = await job_repo.get_by_id(created_job.job_id)

    assert retrieved_job is not None
    assert retrieved_job.status == JobStatus.FINISHED
    assert retrieved_job.progress_percentage == 100.0
    assert retrieved_job.result_data is not None


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.requires_db
async def test_get_job_status_failed(db_session):
    """Test getting status of a failed job."""
    from loadtester.infrastructure.repositories.job_repository import JobRepository
    from loadtester.domain.entities.domain_entities import Job, JobStatus
    from datetime import datetime
    from uuid import uuid4

    job_repo = JobRepository(db_session)

    # Create failed job
    job = Job(
        job_id=str(uuid4()),
        job_type="load_test",
        status=JobStatus.FAILED,
        error_message="Test execution failed",
        created_at=datetime.utcnow(),
        started_at=datetime.utcnow(),
        finished_at=datetime.utcnow()
    )
    created_job = await job_repo.create(job)

    # Get job status
    retrieved_job = await job_repo.get_by_id(created_job.job_id)

    assert retrieved_job is not None
    assert retrieved_job.status == JobStatus.FAILED
    assert retrieved_job.error_message == "Test execution failed"


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.requires_db
async def test_get_job_status_not_found(db_session):
    """Test getting status of non-existent job."""
    from loadtester.infrastructure.repositories.job_repository import JobRepository

    job_repo = JobRepository(db_session)

    # Try to get non-existent job
    retrieved_job = await job_repo.get_by_id("non-existent-job-id")

    assert retrieved_job is None


# ============================================================================
# INTEGRATION TEST: Job Progress Tracking
# ============================================================================

@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.requires_db
async def test_get_job_status_with_progress(db_session):
    """Test getting job status with progress updates."""
    from loadtester.infrastructure.repositories.job_repository import JobRepository
    from loadtester.domain.entities.domain_entities import Job, JobStatus
    from datetime import datetime
    from uuid import uuid4

    job_repo = JobRepository(db_session)

    # Create job
    job = Job(
        job_id=str(uuid4()),
        job_type="load_test",
        status=JobStatus.RUNNING,
        created_at=datetime.utcnow(),
        started_at=datetime.utcnow()
    )
    created_job = await job_repo.create(job)

    # Update progress multiple times
    progress_values = [10.0, 25.0, 50.0, 75.0, 90.0]
    for progress in progress_values:
        created_job.update_progress(progress)
        await job_repo.update(created_job)

        # Verify progress updated
        retrieved_job = await job_repo.get_by_id(created_job.job_id)
        assert retrieved_job.progress_percentage == progress


# ============================================================================
# INTEGRATION TEST: Endpoint Request Validation
# ============================================================================

@pytest.mark.integration
def test_openapi_spec_request_validation():
    """Test OpenAPI spec request model validation."""
    from loadtester.presentation.api.v1.openapi_endpoints import OpenAPISpecRequest
    from pydantic import ValidationError

    # Valid request
    valid_request = OpenAPISpecRequest(spec_content=VALID_OPENAPI_JSON)
    assert valid_request.spec_content == VALID_OPENAPI_JSON.strip()

    # Invalid request - empty spec
    with pytest.raises(ValidationError):
        OpenAPISpecRequest(spec_content="")

    # Invalid request - whitespace only
    with pytest.raises(ValidationError):
        OpenAPISpecRequest(spec_content="   ")


@pytest.mark.integration
def test_endpoint_info_from_dict():
    """Test EndpointInfo model creation from dict."""
    from loadtester.presentation.api.v1.openapi_endpoints import EndpointInfo

    endpoint_data = {
        "path": "/users",
        "method": "GET",
        "summary": "Get users",
        "description": "Retrieve all users",
        "parameters": [{"name": "id", "in": "path"}],
        "request_body": {},
        "responses": {"200": {"description": "Success"}}
    }

    endpoint_info = EndpointInfo.from_dict(endpoint_data)

    assert endpoint_info.path == "/users"
    assert endpoint_info.method == "GET"
    assert endpoint_info.summary == "Get users"
    assert len(endpoint_info.parameters) == 1


@pytest.mark.integration
def test_endpoint_info_handles_none_values():
    """Test EndpointInfo handles None values properly."""
    from loadtester.presentation.api.v1.openapi_endpoints import EndpointInfo

    endpoint_data = {
        "path": "/test",
        "method": "POST",
        "summary": None,
        "description": None,
        "parameters": None,
        "request_body": None,
        "responses": None
    }

    endpoint_info = EndpointInfo.from_dict(endpoint_data)

    assert endpoint_info.path == "/test"
    assert endpoint_info.method == "POST"
    assert endpoint_info.summary == ""
    assert endpoint_info.description == ""
    assert endpoint_info.parameters == []
    assert endpoint_info.request_body == {}
    assert endpoint_info.responses == {}


# ============================================================================
# INTEGRATION TEST: Service Integration
# ============================================================================

@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.requires_db
async def test_load_test_service_get_job_status(db_session):
    """Test LoadTestService get_job_status method."""
    from loadtester.domain.services.load_test_service import LoadTestService
    from loadtester.infrastructure.repositories.job_repository import JobRepository
    from loadtester.domain.entities.domain_entities import Job, JobStatus
    from unittest.mock import AsyncMock
    from datetime import datetime
    from uuid import uuid4

    # Create mocked dependencies
    job_repo = JobRepository(db_session)

    # Create service with mocked dependencies
    service = LoadTestService(
        api_repository=AsyncMock(),
        endpoint_repository=AsyncMock(),
        scenario_repository=AsyncMock(),
        execution_repository=AsyncMock(),
        result_repository=AsyncMock(),
        job_repository=job_repo,
        openapi_parser=AsyncMock(),
        mock_generator=AsyncMock(),
        k6_generator=AsyncMock(),
        k6_runner=AsyncMock(),
        report_generator=AsyncMock(),
        degradation_settings={}
    )

    # Create job
    job = Job(
        job_id=str(uuid4()),
        job_type="load_test",
        status=JobStatus.RUNNING,
        progress_percentage=50.0,
        created_at=datetime.utcnow(),
        started_at=datetime.utcnow()
    )
    created_job = await job_repo.create(job)

    # Get job status via service
    status_response = await service.get_job_status(created_job.job_id)

    assert status_response["job_id"] == created_job.job_id
    assert status_response["status"] == JobStatus.RUNNING.value
    assert status_response["progress"] == 50.0


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.requires_db
async def test_load_test_service_job_not_found(db_session):
    """Test LoadTestService raises error for non-existent job."""
    from loadtester.domain.services.load_test_service import LoadTestService
    from loadtester.infrastructure.repositories.job_repository import JobRepository
    from loadtester.shared.exceptions.domain_exceptions import ResourceNotFoundError
    from unittest.mock import AsyncMock

    job_repo = JobRepository(db_session)

    service = LoadTestService(
        api_repository=AsyncMock(),
        endpoint_repository=AsyncMock(),
        scenario_repository=AsyncMock(),
        execution_repository=AsyncMock(),
        result_repository=AsyncMock(),
        job_repository=job_repo,
        openapi_parser=AsyncMock(),
        mock_generator=AsyncMock(),
        k6_generator=AsyncMock(),
        k6_runner=AsyncMock(),
        report_generator=AsyncMock(),
        degradation_settings={}
    )

    with pytest.raises(ResourceNotFoundError):
        await service.get_job_status("non-existent-job-id")


# ============================================================================
# REST API ENDPOINT TESTS (FastAPI)
# ============================================================================

@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.requires_db
async def test_create_load_test_success(db_session, mock_ai_client):
    """Test POST /api/v1/load-test - successful load test creation."""
    from fastapi.testclient import TestClient
    from loadtester.presentation.api.v1.api_endpoints import router, LoadTestRequest, EndpointConfigRequest
    from loadtester.domain.services.load_test_service import LoadTestService
    from loadtester.infrastructure.repositories.api_repository import APIRepository
    from loadtester.infrastructure.repositories.endpoint_repository import EndpointRepository
    from loadtester.infrastructure.repositories.test_scenario_repository import TestScenarioRepository
    from loadtester.infrastructure.repositories.test_execution_repository import TestExecutionRepository
    from loadtester.infrastructure.repositories.test_result_repository import TestResultRepository
    from loadtester.infrastructure.repositories.job_repository import JobRepository
    from loadtester.infrastructure.external.local_openapi_parser import LocalOpenAPIParser
    from unittest.mock import AsyncMock, MagicMock
    from fastapi import FastAPI, BackgroundTasks

    # Create FastAPI app for testing
    app = FastAPI()
    app.include_router(router, prefix="/api/v1")

    # Create mock service
    mock_service = AsyncMock(spec=LoadTestService)
    mock_job = MagicMock()
    mock_job.job_id = "test-job-123"
    mock_job.status.value = "PENDING"
    mock_service.create_load_test_job = AsyncMock(return_value=mock_job)

    # Override dependency
    from loadtester.infrastructure.config.dependencies import get_custom_load_test_service
    app.dependency_overrides[get_custom_load_test_service] = lambda: mock_service

    # Create request
    request_data = {
        "api_spec": VALID_OPENAPI_JSON,
        "selected_endpoints": [
            {
                "path": "/users",
                "method": "GET",
                "expected_volumetry": 1000,
                "expected_concurrent_users": 50,
                "use_mock_data": True
            }
        ],
        "test_name": "Test API Load Test"
    }

    # Make request using TestClient
    with TestClient(app) as client:
        response = client.post("/api/v1/load-test", json=request_data)

    assert response.status_code == 202
    response_data = response.json()
    assert response_data["job_id"] == "test-job-123"
    assert response_data["status"] == "PENDING"
    assert "/status/" in response_data["status_url"]
    assert "created and started" in response_data["message"].lower()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_load_test_invalid_config():
    """Test POST /api/v1/load-test - invalid configuration."""
    from fastapi.testclient import TestClient
    from loadtester.presentation.api.v1.api_endpoints import router
    from unittest.mock import AsyncMock
    from fastapi import FastAPI

    app = FastAPI()
    app.include_router(router, prefix="/api/v1")

    # Mock the dependency to avoid AI client initialization
    mock_service = AsyncMock()
    from loadtester.infrastructure.config.dependencies import get_custom_load_test_service
    app.dependency_overrides[get_custom_load_test_service] = lambda: mock_service

    # Invalid request - empty api_spec
    request_data = {
        "api_spec": "",
        "selected_endpoints": [
            {
                "path": "/users",
                "method": "GET",
                "expected_volumetry": 1000,
                "expected_concurrent_users": 50
            }
        ]
    }

    with TestClient(app) as client:
        response = client.post("/api/v1/load-test", json=request_data)

    assert response.status_code == 422  # Validation error


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.requires_db
async def test_create_load_test_concurrent_limit(db_session):
    """Test POST /api/v1/load-test - concurrent job limit exceeded."""
    from fastapi.testclient import TestClient
    from loadtester.presentation.api.v1.api_endpoints import router
    from loadtester.shared.exceptions.domain_exceptions import LoadTestExecutionError
    from unittest.mock import AsyncMock
    from fastapi import FastAPI

    app = FastAPI()
    app.include_router(router, prefix="/api/v1")

    # Mock service that raises concurrent limit error
    mock_service = AsyncMock()
    mock_service.create_load_test_job = AsyncMock(
        side_effect=LoadTestExecutionError("Maximum concurrent jobs limit reached")
    )

    from loadtester.infrastructure.config.dependencies import get_custom_load_test_service
    app.dependency_overrides[get_custom_load_test_service] = lambda: mock_service

    request_data = {
        "api_spec": VALID_OPENAPI_JSON,
        "selected_endpoints": [
            {
                "path": "/users",
                "method": "GET",
                "expected_volumetry": 1000,
                "expected_concurrent_users": 50
            }
        ]
    }

    with TestClient(app) as client:
        response = client.post("/api/v1/load-test", json=request_data)

    assert response.status_code == 409  # Conflict
    assert "concurrent" in response.json()["detail"].lower()


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.requires_db
async def test_download_report_success(db_session, tmp_path):
    """Test GET /api/v1/report/{job_id} - successful report download."""
    from fastapi.testclient import TestClient
    from loadtester.presentation.api.v1.report_endpoints import router
    from unittest.mock import AsyncMock, patch
    from fastapi import FastAPI
    from pathlib import Path

    app = FastAPI()
    app.include_router(router, prefix="/api/v1")

    # Create a fake PDF report
    report_path = tmp_path / "loadtest_report_test-job-123.pdf"
    report_path.write_text("Fake PDF content")

    # Mock service
    mock_service = AsyncMock()
    mock_service.get_job_status = AsyncMock(return_value={
        "job_id": "test-job-123",
        "status": "FINISHED",
        "report_url": "/api/v1/report/test-job-123"
    })

    from loadtester.infrastructure.config.dependencies import get_load_test_service
    app.dependency_overrides[get_load_test_service] = lambda: mock_service

    # Mock settings to use tmp_path
    with patch("loadtester.presentation.api.v1.report_endpoints.get_settings") as mock_settings:
        mock_settings.return_value.reports_path = str(tmp_path)

        with TestClient(app) as client:
            response = client.get("/api/v1/report/test-job-123")

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.requires_db
async def test_download_report_not_ready(db_session):
    """Test GET /api/v1/report/{job_id} - report not ready (job still running)."""
    from fastapi.testclient import TestClient
    from loadtester.presentation.api.v1.report_endpoints import router
    from unittest.mock import AsyncMock
    from fastapi import FastAPI

    app = FastAPI()
    app.include_router(router, prefix="/api/v1")

    # Mock service - job still running
    mock_service = AsyncMock()
    mock_service.get_job_status = AsyncMock(return_value={
        "job_id": "test-job-456",
        "status": "RUNNING",
        "progress": 50.0
    })

    from loadtester.infrastructure.config.dependencies import get_load_test_service
    app.dependency_overrides[get_load_test_service] = lambda: mock_service

    with TestClient(app) as client:
        response = client.get("/api/v1/report/test-job-456")

    assert response.status_code == 400
    assert "not available" in response.json()["detail"].lower()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_download_report_not_found():
    """Test GET /api/v1/report/{job_id} - job not found."""
    from fastapi.testclient import TestClient
    from loadtester.presentation.api.v1.report_endpoints import router
    from unittest.mock import AsyncMock
    from fastapi import FastAPI

    app = FastAPI()
    app.include_router(router, prefix="/api/v1")

    # Mock service - job not found
    mock_service = AsyncMock()
    mock_service.get_job_status = AsyncMock(side_effect=Exception("Job not found"))

    from loadtester.infrastructure.config.dependencies import get_load_test_service
    app.dependency_overrides[get_load_test_service] = lambda: mock_service

    with TestClient(app) as client:
        response = client.get("/api/v1/report/non-existent-job")

    assert response.status_code == 500  # Internal server error


@pytest.mark.integration
@pytest.mark.asyncio
async def test_health_check():
    """Test GET /api/v1/health - health check endpoint."""
    from fastapi.testclient import TestClient
    from loadtester.presentation.api.v1.status_endpoints import router
    from unittest.mock import patch
    from fastapi import FastAPI

    app = FastAPI()
    app.include_router(router, prefix="/api/v1")

    # Mock settings
    with patch("loadtester.presentation.api.v1.status_endpoints.get_settings") as mock_settings:
        mock_settings.return_value.app_name = "LoadTester"
        mock_settings.return_value.app_version = "1.0.0"

        with TestClient(app) as client:
            response = client.get("/api/v1/health")

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["status"] == "healthy"
    assert response_data["service"] == "LoadTester"
    assert response_data["version"] == "1.0.0"
    assert "timestamp" in response_data
