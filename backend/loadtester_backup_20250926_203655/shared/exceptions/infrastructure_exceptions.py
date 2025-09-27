"""
Infrastructure-specific Exceptions
External dependencies and infrastructure related exceptions
"""

from typing import Any, Dict, Optional

from .base import LoadTesterException


class DatabaseError(LoadTesterException):
    """Raised when database operations fail."""
    
    def __init__(
        self,
        message: str,
        operation: Optional[str] = None,
        table: Optional[str] = None
    ):
        details = {}
        if operation:
            details["operation"] = operation
        if table:
            details["table"] = table
        
        super().__init__(
            message=message,
            error_type="database_error",
            status_code=500,
            details=details
        )


class NotFoundError(LoadTesterException):
    """Raised when a database record is not found."""
    
    def __init__(
        self,
        message: str,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None
    ):
        details = {}
        if entity_type:
            details["entity_type"] = entity_type
        if entity_id:
            details["entity_id"] = entity_id
        
        super().__init__(
            message=message,
            error_type="not_found",
            status_code=404,
            details=details
        )


class ExternalServiceError(LoadTesterException):
    """Raised when external service calls fail."""
    
    def __init__(
        self,
        message: str,
        service_name: Optional[str] = None,
        status_code: Optional[int] = None,
        response_body: Optional[str] = None
    ):
        details = {}
        if service_name:
            details["service_name"] = service_name
        if status_code:
            details["external_status_code"] = status_code
        if response_body:
            details["response_body"] = response_body[:500]  # Limit response body size
        
        super().__init__(
            message=message,
            error_type="external_service_error",
            status_code=502,
            details=details
        )


class AIServiceError(LoadTesterException):
    """Raised when AI service operations fail."""
    
    def __init__(
        self,
        message: str,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        operation: Optional[str] = None
    ):
        details = {}
        if provider:
            details["provider"] = provider
        if model:
            details["model"] = model
        if operation:
            details["operation"] = operation
        
        super().__init__(
            message=message,
            error_type="ai_service_error",
            status_code=502,
            details=details
        )


class FileOperationError(LoadTesterException):
    """Raised when file operations fail."""
    
    def __init__(
        self,
        message: str,
        file_path: Optional[str] = None,
        operation: Optional[str] = None
    ):
        details = {}
        if file_path:
            details["file_path"] = file_path
        if operation:
            details["operation"] = operation
        
        super().__init__(
            message=message,
            error_type="file_operation_error",
            status_code=500,
            details=details
        )


class K6ExecutionError(LoadTesterException):
    """Raised when K6 execution fails."""
    
    def __init__(
        self,
        message: str,
        script_path: Optional[str] = None,
        exit_code: Optional[int] = None,
        stderr: Optional[str] = None
    ):
        details = {}
        if script_path:
            details["script_path"] = script_path
        if exit_code is not None:
            details["exit_code"] = exit_code
        if stderr:
            details["stderr"] = stderr[:1000]  # Limit stderr size
        
        super().__init__(
            message=message,
            error_type="k6_execution_error",
            status_code=500,
            details=details
        )


class ConfigurationError(LoadTesterException):
    """Raised when configuration is invalid or missing."""
    
    def __init__(
        self,
        message: str,
        config_key: Optional[str] = None,
        config_value: Optional[str] = None
    ):
        details = {}
        if config_key:
            details["config_key"] = config_key
        if config_value:
            details["config_value"] = config_value
        
        super().__init__(
            message=message,
            error_type="configuration_error",
            status_code=500,
            details=details
        )


class ResourceLimitError(LoadTesterException):
    """Raised when resource limits are exceeded."""
    
    def __init__(
        self,
        message: str,
        resource_type: Optional[str] = None,
        limit_value: Optional[str] = None,
        current_value: Optional[str] = None
    ):
        details = {}
        if resource_type:
            details["resource_type"] = resource_type
        if limit_value:
            details["limit_value"] = limit_value
        if current_value:
            details["current_value"] = current_value
        
        super().__init__(
            message=message,
            error_type="resource_limit_error",
            status_code=429,
            details=details
        )