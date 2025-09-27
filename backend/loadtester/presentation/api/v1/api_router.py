"""
API Router v1
Main router for LoadTester API v1 endpoints
"""

from fastapi import APIRouter

from loadtester.presentation.api.v1 import api_endpoints as load_test, openapi_endpoints as openapi, report_endpoints as report, status_endpoints as status

# Create main API router
api_router = APIRouter()

# Include endpoint routers
api_router.include_router(
    load_test.router,
    tags=["Load Testing"],
    responses={
        400: {"description": "Bad Request"},
        404: {"description": "Not Found"},
        500: {"description": "Internal Server Error"},
    }
)

api_router.include_router(
    status.router,
    tags=["Job Status"],
    responses={
        404: {"description": "Job Not Found"},
        500: {"description": "Internal Server Error"},
    }
)

api_router.include_router(
    report.router,
    tags=["Reports"],
    responses={
        404: {"description": "Report Not Found"},
        500: {"description": "Internal Server Error"},
    }
)

api_router.include_router(
    openapi.router,
    tags=["OpenAPI"],
    responses={
        400: {"description": "Invalid OpenAPI Specification"},
        500: {"description": "Internal Server Error"},
    }
)