"""
Domain-specific Exceptions
Business logic related exceptions
"""

from typing import Any, Dict, Optional

from .custom_exceptions import LoadTesterException


class InvalidConfigurationError(LoadTesterException):
    """Raised when load test configuration is invalid."""
    
    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            error_type="invalid_configuration",
            status_code=400,
            details=details
        )


class LoadTestExecutionError(LoadTesterException):
    """Raised when load test execution fails."""
    
    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            error_type="execution_error",
            status_code=409,
            details=details
        )


class ResourceNotFoundError(LoadTesterException):
    """Raised when a requested resource is not found."""
    
    def __init__(
        self,
        message: str,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None
    ):
        details = {}
        if resource_type:
            details["resource_type"] = resource_type
        if resource_id:
            details["resource_id"] = resource_id
        
        super().__init__(
            message=message,
            error_type="resource_not_found",
            status_code=404,
            details=details
        )


class BusinessRuleViolationError(LoadTesterException):
    """Raised when a business rule is violated."""
    
    def __init__(
        self,
        message: str,
        rule_name: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        error_details = details or {}
        if rule_name:
            error_details["rule_name"] = rule_name
        
        super().__init__(
            message=message,
            error_type="business_rule_violation",
            status_code=422,
            details=error_details
        )


class DegradationDetectedError(LoadTesterException):
    """Raised when performance degradation is detected."""
    
    def __init__(
        self,
        message: str,
        degradation_type: Optional[str] = None,
        threshold_value: Optional[float] = None,
        actual_value: Optional[float] = None
    ):
        details = {}
        if degradation_type:
            details["degradation_type"] = degradation_type
        if threshold_value is not None:
            details["threshold_value"] = threshold_value
        if actual_value is not None:
            details["actual_value"] = actual_value
        
        super().__init__(
            message=message,
            error_type="degradation_detected",
            status_code=422,
            details=details
        )


class ValidationError(LoadTesterException):
    """Raised when data validation fails."""
    
    def __init__(
        self,
        message: str,
        field_name: Optional[str] = None,
        field_value: Optional[Any] = None,
        validation_rule: Optional[str] = None
    ):
        details = {}
        if field_name:
            details["field_name"] = field_name
        if field_value is not None:
            details["field_value"] = str(field_value)
        if validation_rule:
            details["validation_rule"] = validation_rule
        
        super().__init__(
            message=message,
            error_type="validation_error",
            status_code=400,
            details=details
        )