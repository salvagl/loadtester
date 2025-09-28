"""
Dependency Injection Container
Configuration for dependency injection using dependency-injector
"""

import logging
from dependency_injector import containers, providers
from dependency_injector.wiring import Provide, inject

from loadtester.domain.services.load_test_service import LoadTestService
from loadtester.infrastructure.database.database_connection import DatabaseManager
from loadtester.infrastructure.external.ai_client import MultiProviderAIClient, OpenAPIParserService
from loadtester.infrastructure.external.local_openapi_parser import LocalOpenAPIParser
from loadtester.infrastructure.external.k6_service import K6RunnerService, K6ScriptGeneratorService
from loadtester.infrastructure.external.mock_data_service import MockDataGeneratorService
from loadtester.infrastructure.external.pdf_generator_service import PDFGeneratorService, ReportGeneratorService
from loadtester.infrastructure.repositories.api_repository import APIRepository
from loadtester.infrastructure.repositories.endpoint_repository import EndpointRepository
from loadtester.infrastructure.repositories.job_repository import JobRepository
from loadtester.infrastructure.repositories.test_execution_repository import TestExecutionRepository
from loadtester.infrastructure.repositories.test_result_repository import TestResultRepository
from loadtester.infrastructure.repositories.test_scenario_repository import TestScenarioRepository
from loadtester.settings import Settings

logger = logging.getLogger(__name__)


def create_openapi_parser(config_provider, ai_client_provider):
    """Factory function to create the appropriate OpenAPI parser based on feature flag."""
    # config_provider is actually a dict of settings values
    use_local = config_provider.get('use_local_openapi_parsing', False)
    if use_local:
        return LocalOpenAPIParser()
    else:
        return OpenAPIParserService(ai_client_provider)


class Container(containers.DeclarativeContainer):
    """Dependency injection container."""
    
    # Configuration
    config = providers.Configuration()
    
    # Settings
    settings = providers.Singleton(Settings)
    
    # Database
    database_manager = providers.Singleton(
        DatabaseManager,
        database_url=config.database_url,
    )
    
    # Database session factory
    db_session_factory = providers.Resource(
        database_manager.provided.get_session
    )
    
    # Repositories
    api_repository = providers.Factory(
        APIRepository,
        session=db_session_factory,
    )

    endpoint_repository = providers.Factory(
        EndpointRepository,
        session=db_session_factory,
    )
    
    
    test_scenario_repository = providers.Factory(
        TestScenarioRepository,
        session=db_session_factory,
    )
    
    test_execution_repository = providers.Factory(
        TestExecutionRepository,
        session=db_session_factory,
    )
    
    test_result_repository = providers.Factory(
        TestResultRepository,
        session=db_session_factory,
    )
    
    job_repository = providers.Factory(
        JobRepository,
        session=db_session_factory,
    )
    
    # External Services
    ai_client = providers.Singleton(
        MultiProviderAIClient,
        google_api_key=config.google_api_key,
        anthropic_api_key=config.anthropic_api_key,
        openai_api_key=config.openai_api_key,
    )
    
    # OpenAPI Parser Service (conditional based on feature flag)
    openapi_parser_service = providers.Singleton(
        create_openapi_parser,
        config_provider=config,
        ai_client_provider=ai_client
    )
    
    mock_data_generator_service = providers.Factory(
        MockDataGeneratorService,
        ai_client=ai_client,
    )
    
    k6_script_generator_service = providers.Factory(
        K6ScriptGeneratorService,
        ai_client=ai_client,
    )
    
    k6_runner_service = providers.Singleton(
        K6RunnerService,
        scripts_path=config.k6_scripts_path,
        results_path=config.k6_results_path,
    )
    
    pdf_generator_service = providers.Singleton(
        PDFGeneratorService,
        output_path=config.reports_path,
    )
    
    report_generator_service = providers.Factory(
        ReportGeneratorService,
        ai_client=ai_client,
        pdf_generator=pdf_generator_service,
    )
    
    # Domain Services
    load_test_service = providers.Factory(
        LoadTestService,
        api_repository=api_repository,
        endpoint_repository=endpoint_repository,
        scenario_repository=test_scenario_repository,
        execution_repository=test_execution_repository,
        result_repository=test_result_repository,
        job_repository=job_repository,
        openapi_parser=openapi_parser_service,
        mock_generator=mock_data_generator_service,
        k6_generator=k6_script_generator_service,
        k6_runner=k6_runner_service,
        report_generator=report_generator_service,
        degradation_settings=providers.Dict(
            max_concurrent_jobs=config.max_concurrent_jobs,
            degradation_response_time_multiplier=config.degradation_response_time_multiplier,
            degradation_error_rate_threshold=config.degradation_error_rate_threshold,
            default_test_duration=config.default_test_duration,
            initial_user_percentage=config.initial_user_percentage,
            user_increment_percentage=config.user_increment_percentage,
            stop_error_threshold=config.stop_error_threshold,
        ),
    )





    # Wiring configuration
    wiring_config = containers.WiringConfiguration(
        modules=[
            "loadtester.presentation.api.v1.api_endpoints",
            "loadtester.presentation.api.v1.status_endpoints",
            "loadtester.presentation.api.v1.report_endpoints",
            "loadtester.presentation.api.v1.openapi_endpoints",
        ]
    )
