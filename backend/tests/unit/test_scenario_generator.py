"""
Unit tests for Scenario Generation
Tests the _create_incremental_scenarios method and related logic
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock
from loadtester.domain.services.load_test_service import LoadTestService
from loadtester.domain.entities.domain_entities import TestScenario
from tests.fixtures.mock_data import create_mock_endpoint


# ============================================================================
# TEST FIXTURES
# ============================================================================

@pytest.fixture
def degradation_settings():
    """Degradation settings for tests."""
    return {
        "degradation_response_time_multiplier": 5.0,
        "degradation_error_rate_threshold": 0.5,
        "stop_error_threshold": 0.6,
        "max_concurrent_jobs": 1,
        "default_test_duration": 60
    }


@pytest.fixture
def mock_scenario_repository():
    """Mock scenario repository."""
    repo = MagicMock()

    # Mock create to return the scenario with an ID
    async def create_scenario(scenario):
        scenario.scenario_id = 1
        return scenario

    repo.create = AsyncMock(side_effect=create_scenario)
    return repo


@pytest.fixture
def mock_repositories():
    """Mock all repositories needed by LoadTestService."""
    return {
        "api_repo": MagicMock(),
        "endpoint_repo": MagicMock(),
        "scenario_repo": MagicMock(),
        "execution_repo": MagicMock(),
        "result_repo": MagicMock(),
        "job_repo": MagicMock()
    }


@pytest.fixture
def mock_services():
    """Mock external services."""
    return {
        "openapi_parser": MagicMock(),
        "mock_data_generator": MagicMock(),
        "k6_script_generator": MagicMock(),
        "k6_runner": MagicMock(),
        "pdf_generator": MagicMock()
    }


@pytest.fixture
def load_test_service(degradation_settings, mock_scenario_repository, mock_repositories, mock_services):
    """Create LoadTestService instance with mocked dependencies."""
    service = LoadTestService(
        api_repository=mock_repositories["api_repo"],
        endpoint_repository=mock_repositories["endpoint_repo"],
        scenario_repository=mock_scenario_repository,
        execution_repository=mock_repositories["execution_repo"],
        result_repository=mock_repositories["result_repo"],
        job_repository=mock_repositories["job_repo"],
        openapi_parser=mock_services["openapi_parser"],
        mock_generator=mock_services["mock_data_generator"],
        k6_generator=mock_services["k6_script_generator"],
        k6_runner=mock_services["k6_runner"],
        report_generator=mock_services["pdf_generator"],
        degradation_settings=degradation_settings
    )
    return service


# ============================================================================
# LOAD CALCULATION TESTS
# ============================================================================

@pytest.mark.unit
def test_calculate_load_percentages():
    """Test that correct load percentages are defined."""
    load_percentages = [25, 50, 75, 100, 150, 200]

    assert len(load_percentages) == 6
    assert load_percentages[0] == 25  # Warm-up
    assert load_percentages[-1] == 200  # Stress test
    assert 100 in load_percentages  # Expected load


@pytest.mark.unit
def test_calculate_users_for_percentage():
    """Test calculating concurrent users for different percentages."""
    expected_users = 100

    # Test different load percentages
    assert max(1, int(expected_users * 0.25)) == 25
    assert max(1, int(expected_users * 0.50)) == 50
    assert max(1, int(expected_users * 0.75)) == 75
    assert max(1, int(expected_users * 1.00)) == 100
    assert max(1, int(expected_users * 1.50)) == 150
    assert max(1, int(expected_users * 2.00)) == 200


@pytest.mark.unit
def test_calculate_volumetry_for_percentage():
    """Test calculating volumetry for different percentages."""
    expected_volumetry = 1000

    # Test different load percentages
    assert max(1, int(expected_volumetry * 0.25)) == 250
    assert max(1, int(expected_volumetry * 0.50)) == 500
    assert max(1, int(expected_volumetry * 0.75)) == 750
    assert max(1, int(expected_volumetry * 1.00)) == 1000
    assert max(1, int(expected_volumetry * 1.50)) == 1500
    assert max(1, int(expected_volumetry * 2.00)) == 2000


@pytest.mark.unit
def test_minimum_load_values():
    """Test that load values never go below 1."""
    # Very low expected values
    expected_users = 2
    expected_volumetry = 3

    # Even at 25%, should be at least 1
    users_25 = max(1, int(expected_users * 0.25))
    volumetry_25 = max(1, int(expected_volumetry * 0.25))

    assert users_25 >= 1
    assert volumetry_25 >= 1


# ============================================================================
# SCENARIO CREATION TESTS
# ============================================================================

@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_incremental_scenarios_count(load_test_service):
    """Test that 6 scenarios are created (25%, 50%, 75%, 100%, 150%, 200%)."""
    endpoint = create_mock_endpoint(
        endpoint_id=1,
        expected_concurrent_users=100,
        expected_volumetry=1000
    )
    test_data = [{"test": "data"}]

    scenarios = await load_test_service._create_incremental_scenarios(endpoint, test_data)

    assert len(scenarios) == 6


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_incremental_scenarios_warmup(load_test_service):
    """Test that first scenario is marked as warm-up."""
    endpoint = create_mock_endpoint(
        endpoint_id=1,
        expected_concurrent_users=100,
        expected_volumetry=1000
    )
    test_data = []

    scenarios = await load_test_service._create_incremental_scenarios(endpoint, test_data)

    # First scenario should be warm-up (25%)
    assert "WARM-UP" in scenarios[0].scenario_name
    assert scenarios[0].concurrent_users == 25
    assert scenarios[0].target_volumetry == 250


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_incremental_scenarios_load_progression(load_test_service):
    """Test that scenarios progress through correct load levels."""
    endpoint = create_mock_endpoint(
        endpoint_id=1,
        expected_concurrent_users=100,
        expected_volumetry=1000
    )
    test_data = []

    scenarios = await load_test_service._create_incremental_scenarios(endpoint, test_data)

    # Verify load progression
    expected_users = [25, 50, 75, 100, 150, 200]
    expected_volumetry = [250, 500, 750, 1000, 1500, 2000]

    for i, scenario in enumerate(scenarios):
        assert scenario.concurrent_users == expected_users[i]
        assert scenario.target_volumetry == expected_volumetry[i]


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_incremental_scenarios_naming(load_test_service):
    """Test that scenario names are descriptive."""
    endpoint = create_mock_endpoint(
        endpoint_id=1,
        endpoint_name="GET /users",
        expected_concurrent_users=100,
        expected_volumetry=1000
    )
    test_data = []

    scenarios = await load_test_service._create_incremental_scenarios(endpoint, test_data)

    # First should have WARM-UP
    assert "WARM-UP" in scenarios[0].scenario_name
    assert "25%" in scenarios[0].scenario_name

    # Others should have percentage
    assert "50%" in scenarios[1].scenario_name
    assert "100%" in scenarios[3].scenario_name
    assert "200%" in scenarios[5].scenario_name

    # All should include endpoint name
    for scenario in scenarios:
        assert "GET /users" in scenario.scenario_name


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_incremental_scenarios_descriptions(load_test_service):
    """Test that scenario descriptions include load details."""
    endpoint = create_mock_endpoint(
        endpoint_id=1,
        expected_concurrent_users=100,
        expected_volumetry=1000
    )
    test_data = []

    scenarios = await load_test_service._create_incremental_scenarios(endpoint, test_data)

    # Warm-up should mention it
    assert "Warm-up" in scenarios[0].description

    # All should mention load percentage
    for i, scenario in enumerate(scenarios):
        load_percentage = [25, 50, 75, 100, 150, 200][i]
        assert f"{load_percentage}%" in scenario.description


# ============================================================================
# SCENARIO CONFIGURATION TESTS
# ============================================================================

@pytest.mark.unit
@pytest.mark.asyncio
async def test_scenario_duration_configuration(load_test_service):
    """Test that scenarios use configured duration."""
    endpoint = create_mock_endpoint(endpoint_id=1)
    test_data = []

    scenarios = await load_test_service._create_incremental_scenarios(endpoint, test_data)

    # All scenarios should have configured duration
    for scenario in scenarios:
        assert scenario.duration_seconds == 60


@pytest.mark.unit
@pytest.mark.asyncio
async def test_scenario_ramp_up_down(load_test_service):
    """Test that scenarios have ramp-up and ramp-down periods."""
    endpoint = create_mock_endpoint(endpoint_id=1)
    test_data = []

    scenarios = await load_test_service._create_incremental_scenarios(endpoint, test_data)

    # All scenarios should have ramp periods
    for scenario in scenarios:
        assert scenario.ramp_up_seconds == 10
        assert scenario.ramp_down_seconds == 10


@pytest.mark.unit
@pytest.mark.asyncio
async def test_scenario_test_data_assignment(load_test_service):
    """Test that test data is assigned to scenarios."""
    endpoint = create_mock_endpoint(endpoint_id=1)
    test_data = [{"id": 1}, {"id": 2}, {"id": 3}]

    scenarios = await load_test_service._create_incremental_scenarios(endpoint, test_data)

    # All scenarios should have the test data
    for scenario in scenarios:
        assert scenario.test_data == test_data


@pytest.mark.unit
@pytest.mark.asyncio
async def test_scenario_timestamps(load_test_service):
    """Test that scenarios have creation timestamps."""
    endpoint = create_mock_endpoint(endpoint_id=1)
    test_data = []

    scenarios = await load_test_service._create_incremental_scenarios(endpoint, test_data)

    # All scenarios should have timestamps
    for scenario in scenarios:
        assert scenario.created_at is not None
        assert isinstance(scenario.created_at, datetime)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_scenario_endpoint_association(load_test_service):
    """Test that scenarios are associated with correct endpoint."""
    endpoint = create_mock_endpoint(endpoint_id=42)
    test_data = []

    scenarios = await load_test_service._create_incremental_scenarios(endpoint, test_data)

    # All scenarios should reference the endpoint
    for scenario in scenarios:
        assert scenario.endpoint_id == 42


# ============================================================================
# EDGE CASES TESTS
# ============================================================================

@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_scenarios_with_low_expected_values(load_test_service):
    """Test scenario creation with very low expected values."""
    endpoint = create_mock_endpoint(
        endpoint_id=1,
        expected_concurrent_users=2,
        expected_volumetry=5
    )
    test_data = []

    scenarios = await load_test_service._create_incremental_scenarios(endpoint, test_data)

    # Should still create 6 scenarios
    assert len(scenarios) == 6

    # All should have at least 1 user and 1 volumetry
    for scenario in scenarios:
        assert scenario.concurrent_users >= 1
        assert scenario.target_volumetry >= 1


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_scenarios_with_high_expected_values(load_test_service):
    """Test scenario creation with very high expected values."""
    endpoint = create_mock_endpoint(
        endpoint_id=1,
        expected_concurrent_users=10000,
        expected_volumetry=100000
    )
    test_data = []

    scenarios = await load_test_service._create_incremental_scenarios(endpoint, test_data)

    # Should create 6 scenarios with scaled values
    assert len(scenarios) == 6

    # 200% scenario should be double the expected values
    assert scenarios[5].concurrent_users == 20000
    assert scenarios[5].target_volumetry == 200000


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_scenarios_with_empty_test_data(load_test_service):
    """Test scenario creation with empty test data."""
    endpoint = create_mock_endpoint(endpoint_id=1)
    test_data = []

    scenarios = await load_test_service._create_incremental_scenarios(endpoint, test_data)

    # Should still create scenarios
    assert len(scenarios) == 6

    # Test data should be empty list
    for scenario in scenarios:
        assert scenario.test_data == []


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_scenarios_repository_called(load_test_service, mock_scenario_repository):
    """Test that repository create is called for each scenario."""
    endpoint = create_mock_endpoint(endpoint_id=1)
    test_data = []

    await load_test_service._create_incremental_scenarios(endpoint, test_data)

    # Repository create should be called 6 times (once per scenario)
    assert mock_scenario_repository.create.call_count == 6


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_scenarios_returns_persisted_scenarios(load_test_service):
    """Test that returned scenarios have IDs from repository."""
    endpoint = create_mock_endpoint(endpoint_id=1)
    test_data = []

    scenarios = await load_test_service._create_incremental_scenarios(endpoint, test_data)

    # All returned scenarios should have IDs (set by mock repository)
    for scenario in scenarios:
        assert scenario.scenario_id is not None


# ============================================================================
# INTEGRATION-STYLE TESTS
# ============================================================================

@pytest.mark.unit
@pytest.mark.asyncio
async def test_complete_scenario_generation_workflow(load_test_service):
    """Test complete workflow of generating scenarios."""
    # Arrange
    endpoint = create_mock_endpoint(
        endpoint_id=1,
        endpoint_name="POST /orders",
        expected_concurrent_users=50,
        expected_volumetry=500
    )
    test_data = [{"order_id": i} for i in range(100)]

    # Act
    scenarios = await load_test_service._create_incremental_scenarios(endpoint, test_data)

    # Assert
    assert len(scenarios) == 6

    # Verify first scenario (warm-up 25%)
    assert scenarios[0].concurrent_users == 12  # max(1, int(50 * 0.25)) = 12
    assert scenarios[0].target_volumetry == 125
    assert "WARM-UP" in scenarios[0].scenario_name

    # Verify 100% scenario
    assert scenarios[3].concurrent_users == 50
    assert scenarios[3].target_volumetry == 500
    assert "100%" in scenarios[3].scenario_name

    # Verify stress test (200%)
    assert scenarios[5].concurrent_users == 100
    assert scenarios[5].target_volumetry == 1000
    assert "200%" in scenarios[5].scenario_name

    # All should have test data
    for scenario in scenarios:
        assert len(scenario.test_data) == 100
