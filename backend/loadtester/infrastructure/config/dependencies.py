"""
FastAPI Dependencies
Dependency injection functions for FastAPI endpoints
"""

from dependency_injector.wiring import Provide, inject
from fastapi import Depends

from loadtester.domain.services.load_test_service import LoadTestService
from loadtester.infrastructure.config.dependency_container import Container
from typing import Union
from loadtester.infrastructure.external.ai_client import OpenAPIParserService
from loadtester.infrastructure.external.local_openapi_parser import LocalOpenAPIParser
from loadtester.infrastructure.external.k6_service import K6RunnerService
from loadtester.infrastructure.external.pdf_generator_service import ReportGeneratorService


@inject
async def get_load_test_service(
    service: LoadTestService = Depends(Provide[Container.load_test_service])
) -> LoadTestService:
    """Get load test service dependency."""
    return service


@inject
async def get_openapi_parser_service(
    service: Union[OpenAPIParserService, LocalOpenAPIParser] = Depends(Provide[Container.openapi_parser_service])
) -> Union[OpenAPIParserService, LocalOpenAPIParser]:
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