"""
Mock Data Fixtures
Factory functions to create test entities and mock data
"""

from datetime import datetime
from typing import Dict, List, Optional

from loadtester.domain.entities.domain_entities import (
    API, AuthConfig, Endpoint, ExecutionStatus, Job, JobStatus,
    TestExecution, TestResult, TestScenario
)


# ============================================================================
# API FACTORIES
# ============================================================================

def create_mock_api(
    api_id: Optional[int] = None,
    api_name: str = "Test API",
    base_url: str = "https://api.test.example.com",
    description: Optional[str] = "Test API description",
    **kwargs
) -> API:
    """Create a mock API entity for testing."""
    return API(
        api_id=api_id,
        api_name=api_name,
        base_url=base_url,
        description=description,
        created_at=kwargs.get("created_at", datetime.utcnow()),
        updated_at=kwargs.get("updated_at", datetime.utcnow()),
        active=kwargs.get("active", True),
    )


# ============================================================================
# ENDPOINT FACTORIES
# ============================================================================

def create_mock_endpoint(
    endpoint_id: Optional[int] = None,
    api_id: Optional[int] = 1,
    endpoint_name: str = "GET /users",
    http_method: str = "GET",
    endpoint_path: str = "/users",
    expected_volumetry: int = 100,
    expected_concurrent_users: int = 10,
    **kwargs
) -> Endpoint:
    """Create a mock Endpoint entity for testing."""
    return Endpoint(
        endpoint_id=endpoint_id,
        api_id=api_id,
        endpoint_name=endpoint_name,
        http_method=http_method,
        endpoint_path=endpoint_path,
        description=kwargs.get("description", "Test endpoint"),
        expected_volumetry=expected_volumetry,
        expected_concurrent_users=expected_concurrent_users,
        auth_config=kwargs.get("auth_config"),
        timeout_ms=kwargs.get("timeout_ms", 30000),
        schema=kwargs.get("schema"),
        created_at=kwargs.get("created_at", datetime.utcnow()),
        updated_at=kwargs.get("updated_at", datetime.utcnow()),
        active=kwargs.get("active", True),
    )


def create_mock_endpoint_with_path_params(
    endpoint_id: Optional[int] = None,
    api_id: Optional[int] = 1,
) -> Endpoint:
    """Create a mock endpoint with path parameters."""
    return create_mock_endpoint(
        endpoint_id=endpoint_id,
        api_id=api_id,
        endpoint_name="GET /users/{userId}",
        http_method="GET",
        endpoint_path="/users/{userId}",
        schema={
            "parameters": [
                {
                    "name": "userId",
                    "in": "path",
                    "required": True,
                    "schema": {"type": "integer"}
                }
            ]
        }
    )


def create_mock_endpoint_post(
    endpoint_id: Optional[int] = None,
    api_id: Optional[int] = 1,
) -> Endpoint:
    """Create a mock POST endpoint with request body."""
    return create_mock_endpoint(
        endpoint_id=endpoint_id,
        api_id=api_id,
        endpoint_name="POST /users",
        http_method="POST",
        endpoint_path="/users",
        schema={
            "requestBody": {
                "required": True,
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "object",
                            "required": ["name", "email"],
                            "properties": {
                                "name": {"type": "string"},
                                "email": {"type": "string", "format": "email"},
                                "age": {"type": "integer", "minimum": 0}
                            }
                        }
                    }
                }
            }
        }
    )


# ============================================================================
# TEST SCENARIO FACTORIES
# ============================================================================

def create_mock_test_scenario(
    scenario_id: Optional[int] = None,
    endpoint_id: Optional[int] = 1,
    scenario_name: str = "Test Scenario - 100% load",
    target_volumetry: int = 100,
    concurrent_users: int = 10,
    duration_seconds: int = 60,
    **kwargs
) -> TestScenario:
    """Create a mock TestScenario entity for testing."""
    return TestScenario(
        scenario_id=scenario_id,
        endpoint_id=endpoint_id,
        scenario_name=scenario_name,
        description=kwargs.get("description", "Test scenario description"),
        target_volumetry=target_volumetry,
        concurrent_users=concurrent_users,
        duration_seconds=duration_seconds,
        ramp_up_seconds=kwargs.get("ramp_up_seconds", 10),
        ramp_down_seconds=kwargs.get("ramp_down_seconds", 10),
        test_data=kwargs.get("test_data"),
        created_at=kwargs.get("created_at", datetime.utcnow()),
        created_by=kwargs.get("created_by", "test_user"),
        active=kwargs.get("active", True),
    )


def create_mock_incremental_scenarios(
    endpoint_id: int = 1,
    base_volumetry: int = 100,
    base_users: int = 10,
) -> List[TestScenario]:
    """Create a set of 6 incremental test scenarios."""
    load_percentages = [25, 50, 75, 100, 150, 200]
    scenarios = []

    for i, percentage in enumerate(load_percentages):
        users = max(1, int(base_users * (percentage / 100)))
        volumetry = max(1, int(base_volumetry * (percentage / 100)))

        is_warmup = (percentage == 25)
        scenario_name = f"{'WARM-UP ' if is_warmup else ''}Scenario - {percentage}% load ({users} users)"

        scenario = create_mock_test_scenario(
            scenario_id=i + 1,
            endpoint_id=endpoint_id,
            scenario_name=scenario_name,
            target_volumetry=volumetry,
            concurrent_users=users,
        )
        scenarios.append(scenario)

    return scenarios


# ============================================================================
# TEST EXECUTION FACTORIES
# ============================================================================

def create_mock_test_execution(
    execution_id: Optional[int] = None,
    scenario_id: Optional[int] = 1,
    status: ExecutionStatus = ExecutionStatus.FINISHED,
    **kwargs
) -> TestExecution:
    """Create a mock TestExecution entity for testing."""
    return TestExecution(
        execution_id=execution_id,
        scenario_id=scenario_id,
        execution_name=kwargs.get("execution_name", "Test Execution"),
        status=status,
        executed_by=kwargs.get("executed_by", "test_user"),
        start_time=kwargs.get("start_time", datetime.utcnow()),
        end_time=kwargs.get("end_time", datetime.utcnow()),
        actual_duration_seconds=kwargs.get("actual_duration_seconds", 60),
        k6_script_used=kwargs.get("k6_script_used"),
        execution_logs=kwargs.get("execution_logs"),
    )


# ============================================================================
# TEST RESULT FACTORIES
# ============================================================================

def create_mock_test_result(
    result_id: Optional[int] = None,
    execution_id: Optional[int] = 1,
    avg_response_time_ms: float = 150.0,
    p95_response_time_ms: float = 300.0,
    success_rate_percent: float = 99.0,
    total_requests: int = 1000,
    **kwargs
) -> TestResult:
    """Create a mock TestResult entity for testing."""
    failed_requests = int(total_requests * (100 - success_rate_percent) / 100)
    successful_requests = total_requests - failed_requests

    return TestResult(
        result_id=result_id,
        execution_id=execution_id,
        avg_response_time_ms=avg_response_time_ms,
        p95_response_time_ms=p95_response_time_ms,
        p99_response_time_ms=kwargs.get("p99_response_time_ms", p95_response_time_ms * 1.2),
        min_response_time_ms=kwargs.get("min_response_time_ms", 50.0),
        max_response_time_ms=kwargs.get("max_response_time_ms", 500.0),
        total_requests=total_requests,
        successful_requests=successful_requests,
        failed_requests=failed_requests,
        success_rate_percent=success_rate_percent,
        requests_per_second=kwargs.get("requests_per_second", 16.67),
        data_sent_kb=kwargs.get("data_sent_kb", 100.0),
        data_received_kb=kwargs.get("data_received_kb", 500.0),
    )


def create_mock_degraded_result(
    result_id: Optional[int] = None,
    execution_id: Optional[int] = 1,
) -> TestResult:
    """Create a mock TestResult with degraded performance."""
    return create_mock_test_result(
        result_id=result_id,
        execution_id=execution_id,
        avg_response_time_ms=2000.0,  # Very high response time
        p95_response_time_ms=3500.0,
        success_rate_percent=45.0,  # High error rate
        total_requests=1000,
    )


# ============================================================================
# JOB FACTORIES
# ============================================================================

def create_mock_job(
    job_id: Optional[str] = None,
    status: JobStatus = JobStatus.PENDING,
    **kwargs
) -> Job:
    """Create a mock Job entity for testing."""
    if job_id is None:
        job_id = "test-job-123"

    return Job(
        job_id=job_id,
        job_type=kwargs.get("job_type", "load_test"),
        status=status,
        callback_url=kwargs.get("callback_url"),
        created_at=kwargs.get("created_at", datetime.utcnow()),
        started_at=kwargs.get("started_at"),
        finished_at=kwargs.get("finished_at"),
        progress_percentage=kwargs.get("progress_percentage", 0.0),
        result_data=kwargs.get("result_data"),
        error_message=kwargs.get("error_message"),
    )


# ============================================================================
# AUTH CONFIG FACTORIES
# ============================================================================

def create_mock_bearer_auth() -> AuthConfig:
    """Create a mock Bearer token auth config."""
    return AuthConfig(
        auth_type="bearer_token",
        token="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.test.token"
    )


def create_mock_api_key_auth() -> AuthConfig:
    """Create a mock API key auth config."""
    return AuthConfig(
        auth_type="api_key",
        api_key="sk-test-1234567890",
        header_name="X-API-Key"
    )


# ============================================================================
# K6 RESULT MOCKS
# ============================================================================

def create_mock_k6_results(
    avg_response_time: float = 150.5,
    p95_response_time: float = 300.0,
    total_requests: int = 1000,
    failed_requests: int = 10,
) -> Dict:
    """Create mock K6 execution results."""
    failure_rate = failed_requests / total_requests if total_requests > 0 else 0

    return {
        "metrics": {
            "http_req_duration": {
                "avg": avg_response_time,
                "min": avg_response_time * 0.3,
                "max": avg_response_time * 3.5,
                "p(95)": p95_response_time,
                "p(99)": p95_response_time * 1.5
            },
            "http_reqs": {
                "count": total_requests,
                "rate": total_requests / 60  # Assuming 60s duration
            },
            "http_req_failed": {
                "count": failed_requests,
                "rate": failure_rate
            },
            "data_sent": {"count": 102400},
            "data_received": {"count": 512000}
        },
        "logs": [
            "K6 execution started",
            f"Completed {total_requests} requests",
            f"Failed requests: {failed_requests}",
            "K6 execution completed successfully"
        ]
    }


# ============================================================================
# MOCK DATA FOR LOAD TESTS
# ============================================================================

def create_mock_test_data(count: int = 10) -> List[Dict]:
    """Create mock test data for load testing."""
    data = []
    for i in range(count):
        data.append({
            "path_params": {"id": i + 1},
            "query_params": {"page": 1, "limit": 10},
            "body": {
                "name": f"Test User {i + 1}",
                "email": f"test{i + 1}@example.com",
                "age": 25 + (i % 50)
            }
        })
    return data


# ============================================================================
# LOAD TEST CONFIGURATION MOCK
# ============================================================================

def create_mock_load_test_config() -> Dict:
    """Create mock LoadTestConfiguration data."""
    return {
        "api_spec": '{"openapi": "3.0.0", "info": {"title": "Test", "version": "1.0.0"}, "paths": {}}',
        "selected_endpoints": [
            {
                "path": "/users",
                "method": "GET",
                "expected_volumetry": 100,
                "expected_concurrent_users": 10,
                "timeout_ms": 30000,
                "use_mock_data": True
            }
        ],
        "global_auth": None,
        "callback_url": None,
        "test_name": "Test Load Test"
    }
