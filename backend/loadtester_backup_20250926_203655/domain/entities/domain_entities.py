"""
Domain Entities for LoadTester
Business logic entities independent of infrastructure
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional
from uuid import UUID, uuid4


class JobStatus(Enum):
    """Job status enumeration."""
    PENDING = "PENDING"
    RUNNING = "RUNNING" 
    FINISHED = "FINISHED"
    FAILED = "FAILED"


class ExecutionStatus(Enum):
    """Test execution status enumeration."""
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    FINISHED = "FINISHED"
    FAILED = "FAILED"


class AuthType(Enum):
    """Authentication type enumeration."""
    BEARER_TOKEN = "bearer_token"
    API_KEY = "api_key"
    NONE = "none"


@dataclass
class API:
    """API domain entity."""
    api_id: Optional[int] = None
    api_name: str = ""
    base_url: str = ""
    description: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    active: bool = True
    endpoints: List["Endpoint"] = field(default_factory=list)


@dataclass
class AuthConfig:
    """Authentication configuration."""
    auth_type: AuthType
    token: Optional[str] = None
    api_key: Optional[str] = None
    header_name: Optional[str] = None  # For API key in header
    query_param_name: Optional[str] = None  # For API key in query


@dataclass
class Endpoint:
    """Endpoint domain entity."""
    endpoint_id: Optional[int] = None
    api_id: Optional[int] = None
    endpoint_name: str = ""
    http_method: str = ""
    endpoint_path: str = ""
    description: Optional[str] = None
    expected_volumetry: Optional[int] = None
    expected_concurrent_users: Optional[int] = None
    auth_config: Optional[AuthConfig] = None
    headers_config: Optional[Dict[str, str]] = None
    payload_template: Optional[Dict] = None
    timeout_ms: int = 30000
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    active: bool = True
    test_scenarios: List["TestScenario"] = field(default_factory=list)


@dataclass
class TestScenario:
    """Test scenario domain entity."""
    scenario_id: Optional[int] = None
    endpoint_id: Optional[int] = None
    scenario_name: str = ""
    description: Optional[str] = None
    target_volumetry: int = 0
    concurrent_users: int = 0
    duration_seconds: int = 60
    ramp_up_seconds: int = 10
    ramp_down_seconds: int = 10
    k6_options: Optional[Dict] = None
    test_data: Optional[List[Dict]] = None
    created_at: Optional[datetime] = None
    created_by: str = "system"
    active: bool = True
    test_executions: List["TestExecution"] = field(default_factory=list)


@dataclass
class TestExecution:
    """Test execution domain entity."""
    execution_id: Optional[int] = None
    scenario_id: Optional[int] = None
    execution_name: str = ""
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    status: ExecutionStatus = ExecutionStatus.PENDING
    actual_duration_seconds: Optional[int] = None
    k6_script_used: Optional[str] = None
    execution_logs: Optional[str] = None
    executed_by: str = "system"
    test_result: Optional["TestResult"] = None


@dataclass
class ErrorDetail:
    """Error detail domain entity."""
    error_id: Optional[int] = None
    result_id: Optional[int] = None
    error_type: str = ""
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    error_count: int = 0
    error_percentage: Optional[float] = None


@dataclass
class PerformanceMetric:
    """Performance metric domain entity."""
    metric_id: Optional[int] = None
    result_id: Optional[int] = None
    metric_name: str = ""
    metric_type: str = ""
    metric_value: float = 0.0
    unit_of_measure: str = ""
    timestamp_collected: Optional[datetime] = None


@dataclass
class TestResult:
    """Test result domain entity."""
    result_id: Optional[int] = None
    execution_id: Optional[int] = None
    avg_response_time_ms: Optional[float] = None
    p95_response_time_ms: Optional[float] = None
    p99_response_time_ms: Optional[float] = None
    min_response_time_ms: Optional[float] = None
    max_response_time_ms: Optional[float] = None
    total_requests: Optional[int] = None
    successful_requests: Optional[int] = None
    failed_requests: Optional[int] = None
    success_rate_percent: Optional[float] = None
    requests_per_second: Optional[float] = None
    actual_concurrent_users: Optional[int] = None
    actual_volumetry_used: Optional[int] = None
    data_sent_kb: Optional[float] = None
    data_received_kb: Optional[float] = None
    http_errors_4xx: int = 0
    http_errors_5xx: int = 0
    timeout_errors: int = 0
    connection_errors: int = 0
    error_summary: Optional[str] = None
    error_details: List[ErrorDetail] = field(default_factory=list)
    performance_metrics: List[PerformanceMetric] = field(default_factory=list)
    
    @property
    def has_degradation(self) -> bool:
        """Check if results show degradation based on error rate."""
        if self.success_rate_percent is None:
            return True
        return self.success_rate_percent < 50.0  # 50% success rate threshold
    
    @property
    def error_rate_percent(self) -> float:
        """Calculate error rate percentage."""
        if self.total_requests and self.total_requests > 0:
            return (self.failed_requests or 0) / self.total_requests * 100
        return 0.0


@dataclass
class Job:
    """Job domain entity for tracking long-running operations."""
    job_id: str = field(default_factory=lambda: str(uuid4()))
    job_type: str = ""
    status: JobStatus = JobStatus.PENDING
    progress_percentage: float = 0.0
    result_data: Optional[Dict] = None
    error_message: Optional[str] = None
    callback_url: Optional[str] = None
    callback_sent: bool = False
    created_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    created_by: str = "system"
    
    def start(self) -> None:
        """Mark job as started."""
        self.status = JobStatus.RUNNING
        self.started_at = datetime.utcnow()
    
    def finish(self, result_data: Optional[Dict] = None) -> None:
        """Mark job as finished."""
        self.status = JobStatus.FINISHED
        self.progress_percentage = 100.0
        self.finished_at = datetime.utcnow()
        if result_data:
            self.result_data = result_data
    
    def fail(self, error_message: str) -> None:
        """Mark job as failed."""
        self.status = JobStatus.FAILED
        self.error_message = error_message
        self.finished_at = datetime.utcnow()
    
    def update_progress(self, percentage: float) -> None:
        """Update job progress."""
        self.progress_percentage = max(0.0, min(100.0, percentage))


@dataclass
class LoadTestConfiguration:
    """Load test configuration domain entity."""
    api_spec: str  # OpenAPI specification (JSON/YAML string)
    selected_endpoints: List[Dict]  # Selected endpoints with configurations
    global_auth: Optional[AuthConfig] = None
    callback_url: Optional[str] = None
    test_name: Optional[str] = None
    degradation_settings: Optional[Dict] = None
    
    def validate(self) -> List[str]:
        """Validate configuration and return list of errors."""
        errors = []
        
        if not self.api_spec:
            errors.append("API specification is required")
        
        if not self.selected_endpoints:
            errors.append("At least one endpoint must be selected")
        
        for i, endpoint in enumerate(self.selected_endpoints):
            if not endpoint.get("method"):
                errors.append(f"Endpoint {i+1}: HTTP method is required")
            if not endpoint.get("path"):
                errors.append(f"Endpoint {i+1}: Path is required")
            if not endpoint.get("expected_volumetry"):
                errors.append(f"Endpoint {i+1}: Expected volumetry is required")
            if not endpoint.get("expected_concurrent_users"):
                errors.append(f"Endpoint {i+1}: Expected concurrent users is required")
        
        return errors


@dataclass
class DegradationDetectionResult:
    """Result of degradation detection analysis."""
    has_degradation: bool
    degradation_point: Optional[Dict] = None
    baseline_metrics: Optional[Dict] = None
    degraded_metrics: Optional[Dict] = None
    degradation_type: Optional[str] = None  # "response_time", "error_rate", "mixed"
    degradation_severity: Optional[str] = None  # "mild", "moderate", "severe"
    recommendations: List[str] = field(default_factory=list)