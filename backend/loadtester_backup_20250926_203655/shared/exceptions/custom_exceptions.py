"""
Base Exception Classes for LoadTester
Custom exception hierarchy for better error handling
"""

from typing import Any, Dict, Optional


class LoadTesterException(Exception):
    """Base exception for LoadTester application."""
    
    def __init__(
        self,
        message: str,
        error_type: str = "loadtester_error",
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.message = message
        self.error_type = error_type
        self.status_code = status_code
        self.details = details or {}
    
    def __str__(self) -> str:
        return f"{self.error_type}: {self.message}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for JSON responses."""
        return {
            "error_type": self.error_type,
            "message": self.message,
            "status_code": self.status_code,
            "details": self.details,
        }