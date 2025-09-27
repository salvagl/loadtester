"""
Collection of __init__.py files for the LoadTester project structure.
Create these files in their respective directories.
"""

# backend/app/domain/__init__.py
DOMAIN_INIT = """
\"\"\"
Domain Layer
Business logic and entities for LoadTester
\"\"\"
"""

# backend/app/domain/entities/__init__.py
DOMAIN_ENTITIES_INIT = """
\"\"\"
Domain Entities
Business entities and value objects
\"\"\"

from .test_scenario import (
    API, AuthConfig, AuthType, DegradationDetectionResult, Endpoint, 
    ExecutionStatus, Job, JobStatus, LoadTestConfiguration, TestExecution, 
    TestResult, TestScenario
)

__all__ = [
    'API', 'AuthConfig', 'AuthType', 'DegradationDetectionResult', 'Endpoint',
    'ExecutionStatus', 'Job', 'JobStatus', 'LoadTestConfiguration', 'TestExecution',
    'TestResult', 'TestScenario'
]
"""

# backend/app/domain/interfaces/__init__.py
DOMAIN_INTERFACES_INIT = """
\"\"\"
Domain Interfaces
Abstract interfaces for services and repositories
\"\"\"
"""

# backend/app/domain/services/__init__.py
DOMAIN_SERVICES_INIT = """
\"\"\"
Domain Services
Business logic services
\"\"\"

from .load_test_service import LoadTestService

__all__ = ['LoadTestService']
"""

# backend/app/infrastructure/__init__.py
INFRASTRUCTURE_INIT = """
\"\"\"
Infrastructure Layer
External dependencies and data access
\"\"\"
"""

# backend/app/infrastructure/database/__init__.py
INFRASTRUCTURE_DATABASE_INIT = """
\"\"\"
Database Infrastructure
Database connection and models
\"\"\"

from .connection import DatabaseManager, get_db_session, get_database_manager
from .models import Base

__all__ = ['DatabaseManager', 'get_db_session', 'get_database_manager', 'Base']
"""

# backend/app/infrastructure/repositories/__init__.py
INFRASTRUCTURE_REPOSITORIES_INIT = """
\"\"\"
Repository Implementations
SQLAlchemy implementations of repository interfaces
\"\"\"

from .api_repository import APIRepository
from .endpoint_repository import EndpointRepository
from .job_repository import JobRepository
from .test_execution_repository import TestExecutionRepository
from .test_result_repository import TestResultRepository
from .test_scenario_repository import TestScenarioRepository

__all__ = [
    'APIRepository', 'EndpointRepository', 'JobRepository',
    'TestExecutionRepository', 'TestResultRepository', 'TestScenarioRepository'
]
"""

# backend/app/infrastructure/external/__init__.py
INFRASTRUCTURE_EXTERNAL_INIT = """
\"\"\"
External Services
AI services, K6 integration, and other external dependencies
\"\"\"

from .ai_client import MultiProviderAIClient, OpenAPIParserService
from .k6_runner import K6RunnerService, K6ScriptGeneratorService
from .pdf_generator import PDFGeneratorService, ReportGeneratorService

__all__ = [
    'MultiProviderAIClient', 'OpenAPIParserService',
    'K6RunnerService', 'K6ScriptGeneratorService',
    'PDFGeneratorService', 'ReportGeneratorService'
]
"""

# backend/app/infrastructure/config/__init__.py
INFRASTRUCTURE_CONFIG_INIT = """
\"\"\"
Configuration and Dependency Injection
Application configuration and DI container
\"\"\"

from .container import Container
from .dependencies import (
    get_load_test_service, get_openapi_parser_service,
    get_k6_runner_service, get_report_generator_service
)

__all__ = [
    'Container', 'get_load_test_service', 'get_openapi_parser_service',
    'get_k6_runner_service', 'get_report_generator_service'
]
"""

# backend/app/presentation/__init__.py
PRESENTATION_INIT = """
\"\"\"
Presentation Layer
FastAPI endpoints and middleware
\"\"\"
"""

# backend/app/presentation/api/__init__.py
PRESENTATION_API_INIT = """
\"\"\"
API Layer
REST API endpoints
\"\"\"
"""

# backend/app/presentation/api/v1/__init__.py
PRESENTATION_API_V1_INIT = """
\"\"\"
API Version 1
LoadTester REST API v1
\"\"\"

from .router import api_router

__all__ = ['api_router']
"""

# backend/app/presentation/api/v1/endpoints/__init__.py
PRESENTATION_ENDPOINTS_INIT = """
\"\"\"
API Endpoints
Individual endpoint modules
\"\"\"
"""

# backend/app/presentation/middleware/__init__.py
PRESENTATION_MIDDLEWARE_INIT = """
\"\"\"
Middleware
HTTP middleware for logging, error handling, etc.
\"\"\"

from .error_handler import ErrorHandlerMiddleware
from .logging import LoggingMiddleware

__all__ = ['ErrorHandlerMiddleware', 'LoggingMiddleware']
"""

# backend/app/shared/__init__.py
SHARED_INIT = """
\"\"\"
Shared Components
Utilities, exceptions, and common components
\"\"\"
"""

# backend/app/shared/exceptions/__init__.py
SHARED_EXCEPTIONS_INIT = """
\"\"\"
Custom Exceptions
Application-specific exception classes
\"\"\"

from .base import LoadTesterException
from .domain import (
    InvalidConfigurationError, LoadTestExecutionError, ResourceNotFoundError,
    BusinessRuleViolationError, DegradationDetectedError, ValidationError
)
from .infrastructure import (
    DatabaseError, NotFoundError, ExternalServiceError, AIServiceError,
    FileOperationError, K6ExecutionError, ConfigurationError, ResourceLimitError
)

__all__ = [
    'LoadTesterException', 'InvalidConfigurationError', 'LoadTestExecutionError',
    'ResourceNotFoundError', 'BusinessRuleViolationError', 'DegradationDetectedError',
    'ValidationError', 'DatabaseError', 'NotFoundError', 'ExternalServiceError',
    'AIServiceError', 'FileOperationError', 'K6ExecutionError', 'ConfigurationError',
    'ResourceLimitError'
]
"""

# backend/app/shared/utils/__init__.py
SHARED_UTILS_INIT = """
\"\"\"
Utility Functions
Common utilities and helpers
\"\"\"

from .logger import setup_logging, get_logger

__all__ = ['setup_logging', 'get_logger']
"""

# backend/app/shared/constants/__init__.py
SHARED_CONSTANTS_INIT = """
\"\"\"
Application Constants
Enums and constant values
\"\"\"
"""

# backend/app/tests/__init__.py
TESTS_INIT = """
\"\"\"
Test Suite
Unit and integration tests for LoadTester
\"\"\"
"""

# frontend/components/__init__.py
FRONTEND_COMPONENTS_INIT = """
\"\"\"
Streamlit Components
Reusable UI components for the LoadTester frontend
\"\"\"

from .openapi_parser import OpenAPIParserComponent
from .endpoint_selector import EndpointSelectorComponent
from .test_configurator import TestConfiguratorComponent
from .results_viewer import ResultsViewerComponent

__all__ = [
    'OpenAPIParserComponent', 'EndpointSelectorComponent',
    'TestConfiguratorComponent', 'ResultsViewerComponent'
]
"""

# Print instructions for creating these files
print("""
To create the __init__.py files, run these commands in your project root:

# Backend init files
mkdir -p backend/app/domain/entities backend/app/domain/interfaces backend/app/domain/services
mkdir -p backend/app/infrastructure/database backend/app/infrastructure/repositories
mkdir -p backend/app/infrastructure/external backend/app/infrastructure/config
mkdir -p backend/app/presentation/api/v1/endpoints backend/app/presentation/middleware
mkdir -p backend/app/shared/exceptions backend/app/shared/utils backend/app/shared/constants
mkdir -p backend/app/tests/unit backend/app/tests/integration

# Frontend init files
mkdir -p frontend/components

# Create all __init__.py files with appropriate content
# (Use the content from the variables above)
""")