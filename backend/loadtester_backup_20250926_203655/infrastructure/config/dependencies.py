"""
FastAPI Dependencies
Dependency injection functions for FastAPI endpoints
"""

from dependency_injector.wiring import Provide, inject
from fastapi import Depends

from app.domain.services.load_test_service import LoadTestService
from app.infrastructure.config.container import Container
from app.infrastructure.external.ai_client import OpenAPIParserService
from app.infrastructure.external.k6_runner import K6RunnerService
from app.infrastructure.external.pdf_generator import ReportGeneratorService


@inject
async def get_load_test_service(
    service: LoadTestService = Depends(Provide[Container.load_test_service])
) -> LoadTestService:
    """Get load test service dependency."""
    return service


@inject
async def get_openapi_parser_service(
    service: OpenAPIParserService = Depends(Provide[Container.openapi_parser_service])
) -> OpenAPIParserService:
    """Get OpenAPI parser service dependency."""
    return service


@inject
async def get_k6_runner_service(
    service: K6RunnerService = Depends(Provide[Container.k6_runner_service])
) -> K6RunnerService:
    """Get K6 runner service dependency."""
    return service


@inject
async def get_report_generator_service(
    service: ReportGeneratorService = Depends(Provide[Container.report_generator_service])
) -> ReportGeneratorService:
    """Get report generator service dependency."""
    return service