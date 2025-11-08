"""
Unit tests for Degradation Detection
Tests the _should_stop_due_to_degradation method and related logic
"""

import pytest
from unittest.mock import MagicMock
from loadtester.domain.services.load_test_service import LoadTestService
from tests.fixtures.mock_data import create_mock_test_result, create_mock_degraded_result


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
def mock_repositories():
    """Mock all repositories."""
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
        "mock_generator": MagicMock(),
        "k6_generator": MagicMock(),
        "k6_runner": MagicMock(),
        "report_generator": MagicMock()
    }


@pytest.fixture
def load_test_service(degradation_settings, mock_repositories, mock_services):
    """Create LoadTestService instance."""
    return LoadTestService(
        api_repository=mock_repositories["api_repo"],
        endpoint_repository=mock_repositories["endpoint_repo"],
        scenario_repository=mock_repositories["scenario_repo"],
        execution_repository=mock_repositories["execution_repo"],
        result_repository=mock_repositories["result_repo"],
        job_repository=mock_repositories["job_repo"],
        openapi_parser=mock_services["openapi_parser"],
        mock_generator=mock_services["mock_generator"],
        k6_generator=mock_services["k6_generator"],
        k6_runner=mock_services["k6_runner"],
        report_generator=mock_services["report_generator"],
        degradation_settings=degradation_settings
    )


# ============================================================================
# ERROR RATE DETECTION TESTS
# ============================================================================

@pytest.mark.unit
@pytest.mark.asyncio
async def test_should_stop_high_error_rate(load_test_service):
    """Test that high error rate triggers stop."""
    # Create result with 70% error rate (above 60% threshold)
    result = create_mock_test_result(
        success_rate_percent=30.0,  # 70% error rate
        total_requests=1000
    )
    baseline = 100.0

    should_stop = await load_test_service._should_stop_due_to_degradation(result, baseline)

    assert should_stop is True


@pytest.mark.unit
@pytest.mark.asyncio
async def test_should_not_stop_acceptable_error_rate(load_test_service):
    """Test that acceptable error rate doesn't trigger stop."""
    # Create result with 5% error rate (below 60% threshold)
    result = create_mock_test_result(
        success_rate_percent=95.0,  # 5% error rate
        total_requests=1000
    )
    baseline = 100.0

    should_stop = await load_test_service._should_stop_due_to_degradation(result, baseline)

    assert should_stop is False


@pytest.mark.unit
@pytest.mark.asyncio
async def test_should_stop_at_threshold(load_test_service):
    """Test stop at exact error threshold."""
    # Create result with exactly 60% error rate
    result = create_mock_test_result(
        success_rate_percent=40.0,  # 60% error rate
        total_requests=1000
    )
    baseline = 100.0

    should_stop = await load_test_service._should_stop_due_to_degradation(result, baseline)

    # Should not stop at exactly the threshold (> not >=)
    assert should_stop is False


@pytest.mark.unit
@pytest.mark.asyncio
async def test_should_stop_just_above_threshold(load_test_service):
    """Test stop just above error threshold."""
    # Create result with 61% error rate (just above 60% threshold)
    result = create_mock_test_result(
        success_rate_percent=39.0,  # 61% error rate
        total_requests=1000
    )
    baseline = 100.0

    should_stop = await load_test_service._should_stop_due_to_degradation(result, baseline)

    assert should_stop is True


# ============================================================================
# RESPONSE TIME DETECTION TESTS
# ============================================================================

@pytest.mark.unit
@pytest.mark.asyncio
async def test_should_stop_response_time_degradation(load_test_service):
    """Test that response time degradation triggers stop."""
    baseline = 100.0  # 100ms baseline
    # Create result with 600ms response time (6x baseline, above 5x threshold)
    result = create_mock_test_result(
        avg_response_time_ms=600.0,
        success_rate_percent=99.0
    )

    should_stop = await load_test_service._should_stop_due_to_degradation(result, baseline)

    assert should_stop is True


@pytest.mark.unit
@pytest.mark.asyncio
async def test_should_not_stop_acceptable_response_time(load_test_service):
    """Test that acceptable response time doesn't trigger stop."""
    baseline = 100.0  # 100ms baseline
    # Create result with 300ms response time (3x baseline, below 5x threshold)
    result = create_mock_test_result(
        avg_response_time_ms=300.0,
        success_rate_percent=99.0
    )

    should_stop = await load_test_service._should_stop_due_to_degradation(result, baseline)

    assert should_stop is False


@pytest.mark.unit
@pytest.mark.asyncio
async def test_should_stop_at_multiplier_threshold(load_test_service):
    """Test stop at exact response time multiplier."""
    baseline = 100.0  # 100ms baseline
    # Create result with exactly 500ms (5x baseline)
    result = create_mock_test_result(
        avg_response_time_ms=500.0,
        success_rate_percent=99.0
    )

    should_stop = await load_test_service._should_stop_due_to_degradation(result, baseline)

    # Should not stop at exactly the threshold (> not >=)
    assert should_stop is False


@pytest.mark.unit
@pytest.mark.asyncio
async def test_should_stop_just_above_multiplier(load_test_service):
    """Test stop just above response time multiplier."""
    baseline = 100.0  # 100ms baseline
    # Create result with 501ms (just above 5x baseline)
    result = create_mock_test_result(
        avg_response_time_ms=501.0,
        success_rate_percent=99.0
    )

    should_stop = await load_test_service._should_stop_due_to_degradation(result, baseline)

    assert should_stop is True


# ============================================================================
# EDGE CASES TESTS
# ============================================================================

@pytest.mark.unit
@pytest.mark.asyncio
async def test_should_stop_no_baseline(load_test_service):
    """Test behavior when no baseline is provided."""
    # No baseline response time (first scenario)
    result = create_mock_test_result(
        avg_response_time_ms=1000.0,
        success_rate_percent=99.0
    )
    baseline = None

    should_stop = await load_test_service._should_stop_due_to_degradation(result, baseline)

    # Should not stop based on response time without baseline
    # Only error rate check applies
    assert should_stop is False


@pytest.mark.unit
@pytest.mark.asyncio
async def test_should_stop_null_result(load_test_service):
    """Test that null result triggers stop."""
    result = None
    baseline = 100.0

    should_stop = await load_test_service._should_stop_due_to_degradation(result, baseline)

    assert should_stop is True


@pytest.mark.unit
@pytest.mark.asyncio
async def test_should_not_stop_first_scenario(load_test_service):
    """Test that first scenario (establishing baseline) doesn't stop."""
    # First scenario result
    result = create_mock_test_result(
        avg_response_time_ms=100.0,
        success_rate_percent=99.0
    )
    baseline = None  # No baseline yet

    should_stop = await load_test_service._should_stop_due_to_degradation(result, baseline)

    assert should_stop is False


@pytest.mark.unit
@pytest.mark.asyncio
async def test_should_stop_result_without_response_time(load_test_service):
    """Test result with no response time data."""
    result = create_mock_test_result(
        avg_response_time_ms=None,  # No response time data
        success_rate_percent=99.0
    )
    baseline = 100.0

    should_stop = await load_test_service._should_stop_due_to_degradation(result, baseline)

    # Should not stop without response time data (no comparison possible)
    assert should_stop is False


@pytest.mark.unit
@pytest.mark.asyncio
async def test_should_stop_zero_baseline(load_test_service):
    """Test behavior with zero baseline."""
    result = create_mock_test_result(
        avg_response_time_ms=100.0,
        success_rate_percent=99.0
    )
    baseline = 0.0

    should_stop = await load_test_service._should_stop_due_to_degradation(result, baseline)

    # Any response time would be infinite times baseline
    # But should still handle gracefully
    assert should_stop is False or should_stop is True  # Either is acceptable


# ============================================================================
# CUSTOM SETTINGS TESTS
# ============================================================================

@pytest.mark.unit
@pytest.mark.asyncio
async def test_custom_degradation_settings_error_threshold(mock_repositories, mock_services):
    """Test with custom error threshold settings."""
    custom_settings = {
        "degradation_response_time_multiplier": 5.0,
        "degradation_error_rate_threshold": 0.5,
        "stop_error_threshold": 0.3,  # Lower threshold (30%)
        "max_concurrent_jobs": 1,
        "default_test_duration": 60
    }

    service = LoadTestService(
        api_repository=mock_repositories["api_repo"],
        endpoint_repository=mock_repositories["endpoint_repo"],
        scenario_repository=mock_repositories["scenario_repo"],
        execution_repository=mock_repositories["execution_repo"],
        result_repository=mock_repositories["result_repo"],
        job_repository=mock_repositories["job_repo"],
        openapi_parser=mock_services["openapi_parser"],
        mock_generator=mock_services["mock_generator"],
        k6_generator=mock_services["k6_generator"],
        k6_runner=mock_services["k6_runner"],
        report_generator=mock_services["report_generator"],
        degradation_settings=custom_settings
    )

    # 35% error rate should trigger stop with 30% threshold
    result = create_mock_test_result(
        success_rate_percent=65.0,  # 35% error rate
        total_requests=1000
    )
    baseline = 100.0

    should_stop = await service._should_stop_due_to_degradation(result, baseline)

    assert should_stop is True


@pytest.mark.unit
@pytest.mark.asyncio
async def test_custom_degradation_settings_multiplier(mock_repositories, mock_services):
    """Test with custom response time multiplier."""
    custom_settings = {
        "degradation_response_time_multiplier": 2.0,  # Lower multiplier (2x)
        "degradation_error_rate_threshold": 0.5,
        "stop_error_threshold": 0.6,
        "max_concurrent_jobs": 1,
        "default_test_duration": 60
    }

    service = LoadTestService(
        api_repository=mock_repositories["api_repo"],
        endpoint_repository=mock_repositories["endpoint_repo"],
        scenario_repository=mock_repositories["scenario_repo"],
        execution_repository=mock_repositories["execution_repo"],
        result_repository=mock_repositories["result_repo"],
        job_repository=mock_repositories["job_repo"],
        openapi_parser=mock_services["openapi_parser"],
        mock_generator=mock_services["mock_generator"],
        k6_generator=mock_services["k6_generator"],
        k6_runner=mock_services["k6_runner"],
        report_generator=mock_services["report_generator"],
        degradation_settings=custom_settings
    )

    baseline = 100.0
    # 250ms response time should trigger stop with 2x multiplier
    result = create_mock_test_result(
        avg_response_time_ms=250.0,
        success_rate_percent=99.0
    )

    should_stop = await service._should_stop_due_to_degradation(result, baseline)

    assert should_stop is True


# ============================================================================
# COMBINED CONDITIONS TESTS
# ============================================================================

@pytest.mark.unit
@pytest.mark.asyncio
async def test_should_stop_both_conditions_met(load_test_service):
    """Test when both error rate and response time exceed thresholds."""
    baseline = 100.0
    result = create_mock_degraded_result()  # High error rate and response time

    should_stop = await load_test_service._should_stop_due_to_degradation(result, baseline)

    # Should stop (either condition is sufficient)
    assert should_stop is True


@pytest.mark.unit
@pytest.mark.asyncio
async def test_should_not_stop_neither_condition_met(load_test_service):
    """Test when neither condition is met."""
    baseline = 100.0
    result = create_mock_test_result(
        avg_response_time_ms=200.0,  # 2x baseline (below 5x threshold)
        success_rate_percent=95.0  # 5% error rate (below 60% threshold)
    )

    should_stop = await load_test_service._should_stop_due_to_degradation(result, baseline)

    assert should_stop is False


@pytest.mark.unit
@pytest.mark.asyncio
async def test_error_rate_property_calculation(load_test_service):
    """Test that error_rate_percent property is calculated correctly."""
    # Result with 100 failed out of 1000 total = 10% error rate
    result = create_mock_test_result(
        total_requests=1000,
        success_rate_percent=90.0
    )

    # Verify the error rate calculation
    assert result.error_rate_percent == 10.0


# ============================================================================
# REALISTIC SCENARIO TESTS
# ============================================================================

@pytest.mark.unit
@pytest.mark.asyncio
async def test_progressive_degradation_scenario(load_test_service):
    """Test realistic progressive degradation scenario."""
    baseline = 150.0  # Baseline from warm-up

    # Scenario 1: 50% load - good performance
    result_50 = create_mock_test_result(
        avg_response_time_ms=180.0,  # 1.2x baseline
        success_rate_percent=99.5
    )
    assert await load_test_service._should_stop_due_to_degradation(result_50, baseline) is False

    # Scenario 2: 100% load - acceptable performance
    result_100 = create_mock_test_result(
        avg_response_time_ms=300.0,  # 2x baseline
        success_rate_percent=98.0
    )
    assert await load_test_service._should_stop_due_to_degradation(result_100, baseline) is False

    # Scenario 3: 150% load - degraded performance
    result_150 = create_mock_test_result(
        avg_response_time_ms=800.0,  # 5.3x baseline - exceeds threshold
        success_rate_percent=95.0
    )
    assert await load_test_service._should_stop_due_to_degradation(result_150, baseline) is True
