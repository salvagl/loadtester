"""
Error Handler Middleware
Global error handling middleware for FastAPI
"""

import logging
import traceback
from typing import Callable

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from loadtester.shared.exceptions.custom_exceptions import LoadTesterException

logger = logging.getLogger(__name__)


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """Middleware to handle exceptions globally."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and handle exceptions."""
        try:
            response = await call_next(request)
            return response
            
        except LoadTesterException as e:
            logger.warning(f"LoadTester exception: {e.error_type} - {e.message}")
            return JSONResponse(
                status_code=e.status_code,
                content={
                    "error": {
                        "type": e.error_type,
                        "message": e.message,
                        "details": e.details,
                    }
                }
            )
            
        except ValueError as e:
            logger.warning(f"Value error: {str(e)}")
            return JSONResponse(
                status_code=400,
                content={
                    "error": {
                        "type": "validation_error",
                        "message": f"Invalid value: {str(e)}",
                        "details": {}
                    }
                }
            )
            
        except Exception as e:
            # Log the full traceback for debugging
            logger.error(f"Unexpected error: {str(e)}")
            logger.error(traceback.format_exc())
            
            # Return generic error response
            return JSONResponse(
                status_code=500,
                content={
                    "error": {
                        "type": "internal_server_error",
                        "message": "An unexpected error occurred",
                        "details": {}
                    }
                }
            )