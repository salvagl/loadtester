"""
Load Test API Endpoints
FastAPI endpoints for load testing operations
"""

import logging
from typing import Dict, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from pydantic import BaseModel, Field, validator

from loadtester.domain.entities.domain_entities import AuthConfig, AuthType, LoadTestConfiguration
from loadtester.domain.services.load_test_service import LoadTestService
from loadtester.infrastructure.config.dependencies import get_load_test_service
from loadtester.shared.exceptions.domain_exceptions import InvalidConfigurationError, LoadTestExecutionError

logger = logging.getLogger(__name__)

router = APIRouter()


# Request/Response Models
class AuthConfigRequest(BaseModel):
    """Authentication configuration request model."""
    auth_type: str = Field(..., description="Authentication type (bearer_token, api_key)")
    token: Optional[str] = Field(None, description="Bearer token")
    api_key: Optional[str] = Field(None, description="API key")
    header_name: Optional[str] = Field(None, description="Header name for API key")
    query_param_name: Optional[str] = Field(None, description="Query parameter name for API key")
    
    @validator("auth_type")
    def validate_auth_type(cls, v):
        valid_types = ["bearer_token", "api_key", "none"]
        if v not in valid_types:
            raise ValueError(f"auth_type must be one of: {valid_types}")
        return v


class EndpointConfigRequest(BaseModel):
    """Endpoint configuration request model."""
    path: str = Field(..., description="Endpoint path")
    method: str = Field(..., description="HTTP method")
    expected_volumetry: int = Field(..., gt=0, description="Expected requests per minute")
    expected_concurrent_users: int = Field(..., gt=0, description="Expected concurrent users")
    timeout_ms: Optional[int] = Field(30000, gt=0, description="Request timeout in milliseconds")
    auth: Optional[AuthConfigRequest] = Field(None, description="Endpoint-specific authentication")
    use_mock_data: bool = Field(True, description="Use auto-generated mock data")
    data_file: Optional[str] = Field(None, description="Path to custom data file")
    
    @validator("method")
    def validate_method(cls, v):
        valid_methods = ["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"]
        if v.upper() not in valid_methods:
            raise ValueError(f"method must be one of: {valid_methods}")
        return v.upper()


class LoadTestRequest(BaseModel):
    """Load test creation request model."""
    api_spec: str = Field(..., description="OpenAPI specification (JSON/YAML string or URL)")
    selected_endpoints: list[EndpointConfigRequest] = Field(
        ..., 
        min_items=1, 
        description="List of endpoints to test"
    )
    global_auth: Optional[AuthConfigRequest] = Field(
        None, 
        description="Global authentication for all endpoints"
    )
    callback_url: Optional[str] = Field(
        None, 
        description="URL to notify when test completes"
    )
    test_name: Optional[str] = Field(None, description="Custom test name")
    
    @validator("api_spec")
    def validate_api_spec(cls, v):
        if not v.strip():
            raise ValueError("api_spec cannot be empty")
        return v.strip()


class LoadTestResponse(BaseModel):
    """Load test creation response model."""
    job_id: str = Field(..., description="Unique job identifier")
    status: str = Field(..., description="Initial job status")
    status_url: str = Field(..., description="URL to check job status")
    message: str = Field(..., description="Success message")


class JobStatusResponse(BaseModel):
    """Job status response model."""
    job_id: str = Field(..., description="Job identifier")
    status: str = Field(..., description="Current job status")
    progress: float = Field(..., description="Progress percentage (0-100)")
    created_at: Optional[str] = Field(None, description="Job creation timestamp")
    started_at: Optional[str] = Field(None, description="Job start timestamp")
    finished_at: Optional[str] = Field(None, description="Job completion timestamp")
    report_url: Optional[str] = Field(None, description="Report download URL (when finished)")
    error_message: Optional[str] = Field(None, description="Error message (when failed)")


# API Endpoints
@router.post(
    "/load-test",
    response_model=LoadTestResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Create Load Test",
    description="Create and start a new load test job"
)
async def create_load_test(
    request: LoadTestRequest,
    background_tasks: BackgroundTasks,
    load_test_service: LoadTestService = Depends(get_load_test_service)
) -> LoadTestResponse:
    """Create a new load test job."""
    try:
        logger.info(f"Creating load test for {len(request.selected_endpoints)} endpoints")
        
        # Convert request to domain configuration
        config = LoadTestConfiguration(
            api_spec=request.api_spec,
            selected_endpoints=[
                {
                    "path": ep.path,
                    "method": ep.method,
                    "expected_volumetry": ep.expected_volumetry,
                    "expected_concurrent_users": ep.expected_concurrent_users,
                    "timeout_ms": ep.timeout_ms,
                    "auth": _convert_auth_config(ep.auth) if ep.auth else None,
                    "use_mock_data": ep.use_mock_data,
                    "data_file": ep.data_file,
                }
                for ep in request.selected_endpoints
            ],
            global_auth=_convert_auth_config(request.global_auth) if request.global_auth else None,
            callback_url=request.callback_url,
            test_name=request.test_name,
        )
        
        # Create job
        job = await load_test_service.create_load_test_job(config)
        
        # Start execution in background
        background_tasks.add_task(
            load_test_service.execute_load_test,
            job.job_id,
            config
        )
        
        logger.info(f"Load test job created: {job.job_id}")
        
        return LoadTestResponse(
            job_id=job.job_id,
            status=job.status.value,
            status_url=f"/api/v1/status/{job.job_id}",
            message="Load test job created and started"
        )
        
    except InvalidConfigurationError as e:
        logger.warning(f"Invalid configuration: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid configuration: {str(e)}"
        )
    
    except LoadTestExecutionError as e:
        logger.warning(f"Load test execution error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    
    except Exception as e:
        logger.error(f"Unexpected error creating load test: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get(
    "/status/{job_id}",
    response_model=JobStatusResponse,
    summary="Get Job Status",
    description="Get the current status and progress of a load test job"
)
async def get_job_status(
    job_id: str,
    load_test_service: LoadTestService = Depends(get_load_test_service)
) -> JobStatusResponse:
    """Get job status and progress."""
    try:
        logger.debug(f"Getting status for job: {job_id}")
        
        status_data = await load_test_service.get_job_status(job_id)
        
        return JobStatusResponse(**status_data)
        
    except Exception as e:
        logger.error(f"Error getting job status {job_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found"
        )


@router.post(
    "/validate-spec",
    summary="Validate OpenAPI Spec",
    description="Validate an OpenAPI specification without creating a test"
)
async def validate_openapi_spec(
    api_spec: str,
    load_test_service: LoadTestService = Depends(get_load_test_service)
) -> Dict[str, bool]:
    """Validate OpenAPI specification."""
    try:
        # This would use the OpenAPI parser service
        # For now, basic validation
        is_valid = len(api_spec.strip()) > 0
        
        return {
            "valid": is_valid,
            "message": "Specification is valid" if is_valid else "Invalid specification"
        }
        
    except Exception as e:
        logger.error(f"Error validating spec: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid OpenAPI specification"
        )


@router.get(
    "/jobs",
    summary="List Jobs",
    description="Get list of load test jobs"
)
async def list_jobs(
    limit: int = 50,
    offset: int = 0,
    status_filter: Optional[str] = None,
    load_test_service: LoadTestService = Depends(get_load_test_service)
) -> Dict:
    """List load test jobs."""
    try:
        # This would be implemented in the service
        # For now, return empty list
        return {
            "jobs": [],
            "total": 0,
            "limit": limit,
            "offset": offset
        }
        
    except Exception as e:
        logger.error(f"Error listing jobs: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving jobs"
        )


def _convert_auth_config(auth_request: Optional[AuthConfigRequest]) -> Optional[AuthConfig]:
    """Convert request auth config to domain auth config."""
    if not auth_request:
        return None
    
    auth_type_map = {
        "bearer_token": AuthType.BEARER_TOKEN,
        "api_key": AuthType.API_KEY,
        "none": AuthType.NONE,
    }
    
    return AuthConfig(
        auth_type=auth_type_map[auth_request.auth_type],
        token=auth_request.token,
        api_key=auth_request.api_key,
        header_name=auth_request.header_name,
        query_param_name=auth_request.query_param_name,
    )