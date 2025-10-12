"""
Database Models for LoadTester
SQLAlchemy models following the specified ER diagram
"""

from datetime import datetime
from typing import List, Optional

from sqlalchemy import (
    Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text, func
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class APIModel(Base):
    """API entity model."""
    
    __tablename__ = "apis"
    
    api_id = Column(Integer, primary_key=True, autoincrement=True)
    api_name = Column(String(200), nullable=False)
    base_url = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    active = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    endpoints = relationship("EndpointModel", back_populates="api", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<API(id={self.api_id}, name='{self.api_name}')>"


class EndpointModel(Base):
    """Endpoint entity model."""

    __tablename__ = "endpoints"

    endpoint_id = Column(Integer, primary_key=True, autoincrement=True)
    api_id = Column(Integer, ForeignKey("apis.api_id"), nullable=False)
    endpoint_name = Column(String(200), nullable=False)
    http_method = Column(String(10), nullable=False)
    endpoint_path = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    expected_volumetry = Column(Integer, nullable=True)
    expected_concurrent_users = Column(Integer, nullable=True)
    auth_type = Column(String(50), nullable=True)  # bearer_token, api_key
    auth_config = Column(Text, nullable=True)  # JSON string with auth configuration
    headers_config = Column(Text, nullable=True)  # JSON string with headers
    payload_template = Column(Text, nullable=True)  # JSON string with payload template
    schema = Column(Text, nullable=True)  # JSON string with OpenAPI schema for the endpoint
    timeout_ms = Column(Integer, default=30000, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    active = Column(Boolean, default=True, nullable=False)

    # Relationships
    api = relationship("APIModel", back_populates="endpoints")
    test_scenarios = relationship("TestScenarioModel", back_populates="endpoint", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<Endpoint(id={self.endpoint_id}, method='{self.http_method}', path='{self.endpoint_path}')>"


class TestScenarioModel(Base):
    """Test scenario entity model."""
    
    __tablename__ = "test_scenarios"
    
    scenario_id = Column(Integer, primary_key=True, autoincrement=True)
    endpoint_id = Column(Integer, ForeignKey("endpoints.endpoint_id"), nullable=False)
    scenario_name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    target_volumetry = Column(Integer, nullable=False)  # requests per minute
    concurrent_users = Column(Integer, nullable=False)
    duration_seconds = Column(Integer, nullable=False)
    ramp_up_seconds = Column(Integer, default=10, nullable=False)
    ramp_down_seconds = Column(Integer, default=10, nullable=False)
    k6_options = Column(Text, nullable=True)  # JSON string with K6 options
    test_data = Column(Text, nullable=True)  # JSON string with test data
    created_at = Column(DateTime, default=func.now(), nullable=False)
    created_by = Column(String(100), default="system", nullable=False)
    active = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    endpoint = relationship("EndpointModel", back_populates="test_scenarios")
    test_executions = relationship("TestExecutionModel", back_populates="scenario", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<TestScenario(id={self.scenario_id}, name='{self.scenario_name}')>"


class TestExecutionModel(Base):
    """Test execution entity model."""
    
    __tablename__ = "test_executions"
    
    execution_id = Column(Integer, primary_key=True, autoincrement=True)
    scenario_id = Column(Integer, ForeignKey("test_scenarios.scenario_id"), nullable=False)
    execution_name = Column(String(200), nullable=False)
    start_time = Column(DateTime, nullable=True)
    end_time = Column(DateTime, nullable=True)
    status = Column(String(20), default="PENDING", nullable=False)  # PENDING, RUNNING, FINISHED, FAILED
    actual_duration_seconds = Column(Integer, nullable=True)
    k6_script_used = Column(Text, nullable=True)  # K6 script that was executed
    execution_logs = Column(Text, nullable=True)  # Execution logs and output
    executed_by = Column(String(100), default="system", nullable=False)
    
    # Relationships
    scenario = relationship("TestScenarioModel", back_populates="test_executions")
    test_result = relationship("TestResultModel", back_populates="execution", uselist=False, cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<TestExecution(id={self.execution_id}, name='{self.execution_name}', status='{self.status}')>"


class TestResultModel(Base):
    """Test result entity model."""
    
    __tablename__ = "test_results"
    
    result_id = Column(Integer, primary_key=True, autoincrement=True)
    execution_id = Column(Integer, ForeignKey("test_executions.execution_id"), nullable=False)
    avg_response_time_ms = Column(Float, nullable=True)
    p95_response_time_ms = Column(Float, nullable=True)
    p99_response_time_ms = Column(Float, nullable=True)
    min_response_time_ms = Column(Float, nullable=True)
    max_response_time_ms = Column(Float, nullable=True)
    total_requests = Column(Integer, nullable=True)
    successful_requests = Column(Integer, nullable=True)
    failed_requests = Column(Integer, nullable=True)
    success_rate_percent = Column(Float, nullable=True)
    requests_per_second = Column(Float, nullable=True)
    actual_concurrent_users = Column(Integer, nullable=True)
    actual_volumetry_used = Column(Integer, nullable=True)
    data_sent_kb = Column(Float, nullable=True)
    data_received_kb = Column(Float, nullable=True)
    http_errors_4xx = Column(Integer, default=0, nullable=False)
    http_errors_5xx = Column(Integer, default=0, nullable=False)
    timeout_errors = Column(Integer, default=0, nullable=False)
    connection_errors = Column(Integer, default=0, nullable=False)
    error_summary = Column(Text, nullable=True)  # JSON string with error summary
    
    # Relationships
    execution = relationship("TestExecutionModel", back_populates="test_result")
    error_details = relationship("ErrorDetailModel", back_populates="result", cascade="all, delete-orphan")
    performance_metrics = relationship("PerformanceMetricModel", back_populates="result", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<TestResult(id={self.result_id}, success_rate={self.success_rate_percent}%)>"


class ErrorDetailModel(Base):
    """Error detail entity model."""
    
    __tablename__ = "error_details"
    
    error_id = Column(Integer, primary_key=True, autoincrement=True)
    result_id = Column(Integer, ForeignKey("test_results.result_id"), nullable=False)
    error_type = Column(String(100), nullable=False)
    error_code = Column(String(20), nullable=True)
    error_message = Column(Text, nullable=True)
    error_count = Column(Integer, nullable=False)
    error_percentage = Column(Float, nullable=True)
    
    # Relationships
    result = relationship("TestResultModel", back_populates="error_details")
    
    def __repr__(self) -> str:
        return f"<ErrorDetail(id={self.error_id}, type='{self.error_type}', count={self.error_count})>"


class PerformanceMetricModel(Base):
    """Performance metric entity model."""
    
    __tablename__ = "performance_metrics"
    
    metric_id = Column(Integer, primary_key=True, autoincrement=True)
    result_id = Column(Integer, ForeignKey("test_results.result_id"), nullable=False)
    metric_name = Column(String(100), nullable=False)
    metric_type = Column(String(50), nullable=False)  # response_time, throughput, error_rate, etc.
    metric_value = Column(Float, nullable=False)
    unit_of_measure = Column(String(20), nullable=False)  # ms, rps, percent, etc.
    timestamp_collected = Column(DateTime, default=func.now(), nullable=False)
    
    # Relationships
    result = relationship("TestResultModel", back_populates="performance_metrics")
    
    def __repr__(self) -> str:
        return f"<PerformanceMetric(id={self.metric_id}, name='{self.metric_name}', value={self.metric_value})>"


# Job tracking model for async operations
class JobModel(Base):
    """Job tracking model for long-running operations."""
    
    __tablename__ = "jobs"
    
    job_id = Column(String(36), primary_key=True)  # UUID
    job_type = Column(String(50), nullable=False)  # load_test, report_generation
    status = Column(String(20), default="PENDING", nullable=False)  # PENDING, RUNNING, FINISHED, FAILED
    progress_percentage = Column(Float, default=0.0, nullable=False)
    result_data = Column(Text, nullable=True)  # JSON string with results
    error_message = Column(Text, nullable=True)
    callback_url = Column(String(500), nullable=True)
    callback_sent = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    started_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)
    created_by = Column(String(100), default="system", nullable=False)
    
    def __repr__(self) -> str:
        return f"<Job(id='{self.job_id}', type='{self.job_type}', status='{self.status}')>"