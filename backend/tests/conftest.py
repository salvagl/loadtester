"""
Pytest Configuration and Global Fixtures
Provides shared fixtures for all tests
"""

import asyncio
import logging
from datetime import datetime
from typing import AsyncGenerator, Dict
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from loadtester.infrastructure.database.database_models import Base

# Disable logging during tests
logging.disable(logging.CRITICAL)


# ============================================================================
# PYTEST CONFIGURATION
# ============================================================================

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# ============================================================================
# DATABASE FIXTURES
# ============================================================================

@pytest_asyncio.fixture
async def db_engine():
    """Create async SQLite in-memory database engine."""
    # Use in-memory SQLite database
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        future=True,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Clean up
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(db_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create async database session for tests."""
    # Create session factory
    async_session_factory = async_sessionmaker(
        bind=db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session_factory() as session:
        try:
            yield session
        finally:
            await session.rollback()
            await session.close()


# ============================================================================
# MOCK SERVICE FIXTURES
# ============================================================================

@pytest.fixture
def mock_ai_client():
    """Mock AI client for data generation."""
    mock = MagicMock()

    # Mock chat completion to return valid JSON
    mock.chat_completion = AsyncMock(
        return_value='[{"path_params": {"id": 1}, "body": {"name": "Test User", "email": "test@example.com"}}]'
    )

    return mock


@pytest.fixture
def mock_k6_runner():
    """Mock K6 runner service."""
    mock = MagicMock()

    # Mock K6 execution with realistic results
    mock.execute_k6_script = AsyncMock(
        return_value={
            "metrics": {
                "http_req_duration": {
                    "avg": 150.5,
                    "min": 50.2,
                    "max": 500.8,
                    "p(95)": 300.0,
                    "p(99)": 450.0
                },
                "http_reqs": {
                    "count": 1000,
                    "rate": 16.67
                },
                "http_req_failed": {
                    "count": 10,
                    "rate": 0.01
                },
                "data_sent": {"count": 102400},
                "data_received": {"count": 512000}
            },
            "logs": ["K6 execution completed successfully"]
        }
    )

    return mock


@pytest.fixture
def mock_k6_generator():
    """Mock K6 script generator service."""
    mock = MagicMock()

    # Mock K6 script generation
    mock.generate_k6_script = AsyncMock(
        return_value="""
        import http from 'k6/http';
        import { check } from 'k6';

        export let options = {
            vus: 10,
            duration: '60s',
        };

        export default function() {
            let res = http.get('https://test.example.com/api/users');
            check(res, { 'status is 200': (r) => r.status === 200 });
        }
        """
    )

    return mock


# ============================================================================
# CONFIGURATION FIXTURES
# ============================================================================

@pytest.fixture
def degradation_settings() -> Dict:
    """Default degradation detection settings."""
    return {
        "degradation_response_time_multiplier": 5.0,
        "degradation_error_rate_threshold": 0.5,
        "stop_error_threshold": 0.6,
        "max_concurrent_jobs": 1,
        "default_test_duration": 60,
        "initial_user_percentage": 0.1,
        "user_increment_percentage": 0.5,
    }


@pytest.fixture
def app_settings() -> Dict:
    """Application settings for tests."""
    return {
        "app_name": "LoadTester",
        "app_version": "0.0.1",
        "log_level": "ERROR",
        "debug": False,
        "max_file_size": 10485760,  # 10MB
        "allowed_file_extensions": [".csv", ".json", ".xlsx"],
    }


# ============================================================================
# TEMPORARY DIRECTORY FIXTURES
# ============================================================================

@pytest.fixture
def temp_report_dir(tmp_path):
    """Temporary directory for PDF reports."""
    report_dir = tmp_path / "reports"
    report_dir.mkdir()
    return str(report_dir)


@pytest.fixture
def temp_data_dir(tmp_path):
    """Temporary directory for test data files."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    return str(data_dir)


@pytest.fixture
def temp_k6_scripts_dir(tmp_path):
    """Temporary directory for K6 scripts."""
    k6_dir = tmp_path / "k6_scripts"
    k6_dir.mkdir()
    return str(k6_dir)


# ============================================================================
# DATETIME FIXTURES
# ============================================================================

@pytest.fixture
def fixed_datetime():
    """Fixed datetime for consistent testing."""
    return datetime(2024, 1, 15, 10, 30, 0)


@pytest.fixture
def freeze_time(monkeypatch, fixed_datetime):
    """Freeze datetime.utcnow() to a fixed value."""
    class FrozenDatetime:
        @staticmethod
        def utcnow():
            return fixed_datetime

    monkeypatch.setattr("loadtester.domain.entities.domain_entities.datetime", FrozenDatetime)
    return fixed_datetime


# ============================================================================
# PYTEST MARKERS
# ============================================================================

def pytest_configure(config):
    """Configure custom pytest markers."""
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "slow: Slow running tests")
    config.addinivalue_line("markers", "requires_db: Tests requiring database")
    config.addinivalue_line("markers", "requires_mock: Tests requiring service mocks")


# ============================================================================
# TEST CLEANUP
# ============================================================================

@pytest.fixture(autouse=True)
async def cleanup_after_test():
    """Cleanup resources after each test."""
    yield
    # Cleanup code here if needed
    await asyncio.sleep(0)  # Allow pending async operations to complete
