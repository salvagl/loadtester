"""
FastAPI Dependencies
Dependency injection functions for FastAPI endpoints
"""

from dependency_injector.wiring import Provide, inject
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from loadtester.domain.services.load_test_service import LoadTestService
from loadtester.infrastructure.config.dependency_container import Container
from loadtester.settings import Settings
from typing import Union
from loadtester.infrastructure.external.ai_client import OpenAPIParserService
from loadtester.infrastructure.external.local_openapi_parser import LocalOpenAPIParser
from loadtester.infrastructure.external.k6_service import K6RunnerService
from loadtester.infrastructure.external.pdf_generator_service import ReportGeneratorService


async def get_database_session() -> AsyncSession:
    """Get database session dependency."""
    from loadtester.infrastructure.database.database_connection import DatabaseManager

    # Create a database manager with the correct settings
    settings = Settings()
    db_manager = DatabaseManager(settings.database_url)

    async for session in db_manager.get_session():
        yield session


async def get_custom_load_test_service(
    db_session: AsyncSession = Depends(get_database_session)
) -> LoadTestService:
    """Get load test service dependency with injected session - custom version."""
    import logging
    from loadtester.infrastructure.repositories.api_repository import APIRepository
    from loadtester.infrastructure.repositories.endpoint_repository import EndpointRepository
    from loadtester.infrastructure.repositories.test_scenario_repository import TestScenarioRepository
    from loadtester.infrastructure.repositories.test_execution_repository import TestExecutionRepository
    from loadtester.infrastructure.repositories.test_result_repository import TestResultRepository
    from loadtester.infrastructure.repositories.job_repository import JobRepository
    from loadtester.infrastructure.external.local_openapi_parser import LocalOpenAPIParser
    from loadtester.infrastructure.external.mock_data_service import MockDataGeneratorService
    from loadtester.infrastructure.external.k6_service import K6ScriptGeneratorService, K6RunnerService
    from loadtester.infrastructure.external.pdf_generator_service import ReportGeneratorService
    from loadtester.infrastructure.external.ai_client import MultiProviderAIClient

    logger = logging.getLogger(__name__)
    logger.info(f"get_custom_load_test_service called with session type: {type(db_session)}")

    try:
        logger.info("Creating repositories...")
        # Create repositories with the session one by one to isolate the issue
        logger.info("Creating APIRepository...")
        api_repository = APIRepository(session=db_session)
        logger.info("Creating EndpointRepository...")
        endpoint_repository = EndpointRepository(session=db_session)
        logger.info("Creating TestScenarioRepository...")
        scenario_repository = TestScenarioRepository(session=db_session)
        logger.info("Creating TestExecutionRepository...")
        execution_repository = TestExecutionRepository(session=db_session)
        logger.info("Creating TestResultRepository...")
        result_repository = TestResultRepository(session=db_session)
        logger.info("Creating JobRepository...")
        job_repository = JobRepository(session=db_session)
        logger.info("All repositories created successfully!")

        logger.info("Getting settings...")
        # Get API keys directly from environment variables
        import os
        google_api_key = os.getenv('GOOGLE_API_KEY')
        anthropic_api_key = os.getenv('ANTHROPIC_API_KEY')
        openai_api_key = os.getenv('OPENAI_API_KEY')

        logger.info(f"Google API Key from env: {google_api_key}")
        logger.info(f"Google API Key configured: {bool(google_api_key)}")
        logger.info(f"Anthropic API Key configured: {bool(anthropic_api_key)}")
        logger.info(f"OpenAI API Key configured: {bool(openai_api_key)}")

        logger.info("About to create AI client...")

        # Create services
        ai_client = MultiProviderAIClient(
            google_api_key=google_api_key,
            anthropic_api_key=anthropic_api_key,
            openai_api_key=openai_api_key
        )
        openapi_parser = LocalOpenAPIParser()
        mock_generator = MockDataGeneratorService(ai_client=ai_client)
        k6_generator = K6ScriptGeneratorService(ai_client=ai_client)
        k6_runner = K6RunnerService(
            scripts_path="/app/k6_scripts",
            results_path="/app/k6_results"
        )
        report_generator = ReportGeneratorService(
            ai_client=ai_client,
            pdf_generator=None  # Will be created later if needed
        )

        # Create service with repositories that have proper sessions
        service = LoadTestService(
            api_repository=api_repository,
            endpoint_repository=endpoint_repository,
            scenario_repository=scenario_repository,
            execution_repository=execution_repository,
            result_repository=result_repository,
            job_repository=job_repository,
            openapi_parser=openapi_parser,
            mock_generator=mock_generator,
            k6_generator=k6_generator,
            k6_runner=k6_runner,
            report_generator=report_generator,
            degradation_settings={
                'max_concurrent_jobs': 3,
                'degradation_response_time_multiplier': 2.0,
                'degradation_error_rate_threshold': 0.05,
                'default_test_duration': 300,
                'initial_user_percentage': 10,
                'user_increment_percentage': 20,
                'stop_error_threshold': 0.1,
            }
        )

        logger.info("LoadTestService created successfully")
        return service

    except Exception as e:
        logger.error(f"Error creating LoadTestService: {e}")
        raise


async def get_load_test_service(
    db_session: AsyncSession = Depends(get_database_session)
) -> LoadTestService:
    """Get load test service dependency - fixed version that properly reads environment variables."""
    # Just delegate to our working custom function
    return await get_custom_load_test_service(db_session)


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