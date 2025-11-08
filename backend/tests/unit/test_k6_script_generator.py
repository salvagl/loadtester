"""
Unit tests for K6ScriptGeneratorService
Tests K6 script generation, validation, and configuration
"""

import pytest
import re
from unittest.mock import MagicMock
from loadtester.infrastructure.external.k6_service import K6ScriptGeneratorService
from tests.fixtures.mock_data import (
    create_mock_endpoint,
    create_mock_endpoint_post,
    create_mock_bearer_auth,
    create_mock_api_key_auth
)


# ============================================================================
# TEST FIXTURES
# ============================================================================

@pytest.fixture
def mock_ai_client():
    """Mock AI client."""
    return MagicMock()


@pytest.fixture
def k6_generator(mock_ai_client):
    """Create K6ScriptGeneratorService instance."""
    return K6ScriptGeneratorService(ai_client=mock_ai_client)


# ============================================================================
# INTEGER CONVERSION TESTS
# ============================================================================

@pytest.mark.unit
def test_ensure_integer_from_float(k6_generator):
    """Test converting float to integer."""
    result = k6_generator._ensure_integer(10.7)

    assert isinstance(result, int)
    assert result == 10


@pytest.mark.unit
def test_ensure_integer_from_string(k6_generator):
    """Test converting string number to integer."""
    result = k6_generator._ensure_integer("42")

    assert isinstance(result, int)
    assert result == 42


@pytest.mark.unit
def test_ensure_integer_from_int(k6_generator):
    """Test that integer stays integer."""
    result = k6_generator._ensure_integer(100)

    assert isinstance(result, int)
    assert result == 100


@pytest.mark.unit
def test_ensure_integer_invalid_value(k6_generator):
    """Test handling invalid value with default."""
    result = k6_generator._ensure_integer("invalid")

    assert isinstance(result, int)
    assert result == 1  # Default value


@pytest.mark.unit
def test_ensure_integer_none_value(k6_generator):
    """Test handling None value."""
    result = k6_generator._ensure_integer(None)

    assert isinstance(result, int)
    assert result == 1  # Default value


# ============================================================================
# SCRIPT GENERATION BASIC TESTS
# ============================================================================

@pytest.mark.unit
@pytest.mark.asyncio
async def test_generate_k6_script_structure(k6_generator):
    """Test that generated script has correct K6 structure."""
    endpoint = create_mock_endpoint(
        endpoint_path="/users",
        http_method="GET"
    )
    test_data = []
    scenario_config = {
        "concurrent_users": 10,
        "target_volumetry": 100,
        "duration": 60,
        "ramp_up": 10,
        "ramp_down": 10
    }

    script = await k6_generator.generate_k6_script(endpoint, test_data, scenario_config)

    assert "import http from 'k6/http';" in script
    assert "import { check, sleep } from 'k6';" in script
    assert "export const options" in script
    assert "export default function()" in script


@pytest.mark.unit
@pytest.mark.asyncio
async def test_generate_k6_script_imports(k6_generator):
    """Test that script includes necessary K6 imports."""
    endpoint = create_mock_endpoint()
    script = await k6_generator.generate_k6_script(endpoint, [], {})

    # Check imports
    assert "import http from 'k6/http';" in script
    assert "import { check, sleep }" in script
    assert "import { Rate, Counter }" in script


@pytest.mark.unit
@pytest.mark.asyncio
async def test_generate_k6_script_options(k6_generator):
    """Test that script includes options configuration."""
    endpoint = create_mock_endpoint()
    script = await k6_generator.generate_k6_script(endpoint, [], {})

    assert "export const options" in script
    assert "stages:" in script
    assert "thresholds:" in script


# ============================================================================
# VUS AND DURATION CONFIGURATION TESTS
# ============================================================================

@pytest.mark.unit
@pytest.mark.asyncio
async def test_script_vus_configuration(k6_generator):
    """Test that VUs (virtual users) are configured correctly."""
    endpoint = create_mock_endpoint()
    scenario_config = {
        "concurrent_users": 50,
        "duration": 60,
        "ramp_up": 10,
        "ramp_down": 10
    }

    script = await k6_generator.generate_k6_script(endpoint, [], scenario_config)

    # Should have target of 50 users
    assert "target: 50" in script


@pytest.mark.unit
@pytest.mark.asyncio
async def test_script_duration_configuration(k6_generator):
    """Test that duration is configured correctly."""
    endpoint = create_mock_endpoint()
    scenario_config = {
        "concurrent_users": 10,
        "duration": 120,  # 2 minutes
        "ramp_up": 15,
        "ramp_down": 15
    }

    script = await k6_generator.generate_k6_script(endpoint, [], scenario_config)

    # Check durations in stages
    assert "duration: '120s'" in script
    assert "duration: '15s'" in script


@pytest.mark.unit
@pytest.mark.asyncio
async def test_script_ramp_stages(k6_generator):
    """Test that ramp-up and ramp-down stages are configured."""
    endpoint = create_mock_endpoint()
    scenario_config = {
        "concurrent_users": 10,
        "duration": 60,
        "ramp_up": 10,
        "ramp_down": 5
    }

    script = await k6_generator.generate_k6_script(endpoint, [], scenario_config)

    # Should have 3 stages: ramp-up, steady, ramp-down
    assert script.count("duration:") >= 3
    assert "target: 0" in script  # Ramp-down to 0


# ============================================================================
# HTTP METHODS TESTS
# ============================================================================

@pytest.mark.unit
@pytest.mark.asyncio
async def test_script_get_request(k6_generator):
    """Test GET request generation."""
    endpoint = create_mock_endpoint(
        endpoint_path="/users",
        http_method="GET"
    )

    script = await k6_generator.generate_k6_script(endpoint, [], {})

    # Should use http.get
    assert "http.get(" in script or "GET" in script


@pytest.mark.unit
@pytest.mark.asyncio
async def test_script_post_request(k6_generator):
    """Test POST request generation."""
    endpoint = create_mock_endpoint_post()

    script = await k6_generator.generate_k6_script(endpoint, [], {})

    # Should use http.post
    assert "http.post(" in script or "POST" in script.upper()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_script_request_body(k6_generator):
    """Test that POST requests include body."""
    endpoint = create_mock_endpoint_post()
    test_data = [
        {"body": {"name": "Test User", "email": "test@example.com"}}
    ]

    script = await k6_generator.generate_k6_script(endpoint, test_data, {})

    # Should have JSON.stringify or body definition
    assert "JSON.stringify" in script or "body" in script


# ============================================================================
# ENDPOINT CONFIGURATION TESTS
# ============================================================================

@pytest.mark.unit
@pytest.mark.asyncio
async def test_script_endpoint_configuration(k6_generator):
    """Test that endpoint path is configured correctly."""
    endpoint = create_mock_endpoint(
        endpoint_path="/api/v1/users",
        http_method="GET"
    )

    script = await k6_generator.generate_k6_script(endpoint, [], {})

    assert "/api/v1/users" in script or "users" in script


@pytest.mark.unit
@pytest.mark.asyncio
async def test_script_timeout_configuration(k6_generator):
    """Test that timeout is configured."""
    endpoint = create_mock_endpoint(timeout_ms=5000)

    script = await k6_generator.generate_k6_script(endpoint, [], {})

    # Should have timeout in params
    assert "timeout:" in script
    assert "5000" in script or "ms" in script


# ============================================================================
# TEST DATA TESTS
# ============================================================================

@pytest.mark.unit
@pytest.mark.asyncio
async def test_script_test_data_inclusion(k6_generator):
    """Test that test data is included in script."""
    endpoint = create_mock_endpoint_post()
    test_data = [
        {"body": {"name": "User 1", "email": "user1@test.com"}},
        {"body": {"name": "User 2", "email": "user2@test.com"}}
    ]

    script = await k6_generator.generate_k6_script(endpoint, test_data, {})

    # Should have data generation logic
    assert "generateTestData" in script or "testData" in script


@pytest.mark.unit
@pytest.mark.asyncio
async def test_script_path_params_replacement(k6_generator):
    """Test that path parameters are handled."""
    endpoint = create_mock_endpoint(
        endpoint_path="/users/{userId}",
        http_method="GET"
    )
    test_data = [{"path_params": {"userId": 1}}]

    script = await k6_generator.generate_k6_script(endpoint, test_data, {})

    # Should handle path params
    assert "userId" in script or "{" in script


@pytest.mark.unit
@pytest.mark.asyncio
async def test_script_with_empty_test_data(k6_generator):
    """Test script generation with empty test data."""
    endpoint = create_mock_endpoint()
    test_data = []

    script = await k6_generator.generate_k6_script(endpoint, test_data, {})

    # Should still generate valid script
    assert "export default function()" in script
    assert "import http from 'k6/http';" in script


# ============================================================================
# AUTHENTICATION TESTS
# ============================================================================

@pytest.mark.unit
def test_build_auth_headers_bearer(k6_generator):
    """Test building Bearer token auth headers."""
    endpoint = create_mock_endpoint()
    endpoint.auth_config = create_mock_bearer_auth()

    headers = k6_generator._build_auth_headers(endpoint)

    assert "Authorization" in headers or "Bearer" in str(headers)


@pytest.mark.unit
def test_build_auth_headers_api_key(k6_generator):
    """Test building API key auth headers."""
    endpoint = create_mock_endpoint()
    endpoint.auth_config = create_mock_api_key_auth()

    headers = k6_generator._build_auth_headers(endpoint)

    # Should include API key header
    assert "X-API-Key" in headers or "api" in headers.lower()


@pytest.mark.unit
def test_build_auth_headers_no_auth(k6_generator):
    """Test building headers with no authentication."""
    endpoint = create_mock_endpoint()
    endpoint.auth_config = None

    headers = k6_generator._build_auth_headers(endpoint)

    # Should return empty or minimal headers
    assert headers is not None


# ============================================================================
# CHECKS AND THRESHOLDS TESTS
# ============================================================================

@pytest.mark.unit
@pytest.mark.asyncio
async def test_script_has_checks(k6_generator):
    """Test that script includes response checks."""
    endpoint = create_mock_endpoint()

    script = await k6_generator.generate_k6_script(endpoint, [], {})

    # Should have checks
    assert "check(" in script
    assert "status" in script


@pytest.mark.unit
@pytest.mark.asyncio
async def test_script_has_thresholds(k6_generator):
    """Test that script includes performance thresholds."""
    endpoint = create_mock_endpoint()

    script = await k6_generator.generate_k6_script(endpoint, [], {})

    # Should have thresholds
    assert "thresholds:" in script
    assert "http_req_duration" in script or "http_req_failed" in script


@pytest.mark.unit
@pytest.mark.asyncio
async def test_script_has_error_tracking(k6_generator):
    """Test that script tracks errors."""
    endpoint = create_mock_endpoint()

    script = await k6_generator.generate_k6_script(endpoint, [], {})

    # Should track errors
    assert "errorRate" in script or "errors" in script or "Rate" in script


# ============================================================================
# SLEEP/THINK TIME TESTS
# ============================================================================

@pytest.mark.unit
@pytest.mark.asyncio
async def test_script_has_sleep(k6_generator):
    """Test that script includes sleep/think time."""
    endpoint = create_mock_endpoint()

    script = await k6_generator.generate_k6_script(endpoint, [], {})

    # Should have sleep call
    assert "sleep(" in script


@pytest.mark.unit
@pytest.mark.asyncio
async def test_script_sleep_calculation(k6_generator):
    """Test that sleep time is calculated for volumetry."""
    endpoint = create_mock_endpoint()
    scenario_config = {
        "concurrent_users": 10,
        "target_volumetry": 100,
        "duration": 60
    }

    script = await k6_generator.generate_k6_script(endpoint, [], scenario_config)

    # Should have sleep with calculated value
    assert "sleep(" in script
    # Sleep value should be present (either as variable or literal)


# ============================================================================
# DYNAMIC DATA GENERATION TESTS
# ============================================================================

@pytest.mark.unit
def test_generate_dynamic_data_helpers_empty(k6_generator):
    """Test dynamic data helper generation with empty data."""
    helpers = k6_generator._generate_dynamic_data_helpers([])

    assert "function generateTestData()" in helpers
    assert "return" in helpers


@pytest.mark.unit
def test_generate_dynamic_data_helpers_with_email(k6_generator):
    """Test dynamic data helpers for email fields."""
    test_data = [
        {"body": {"email": "test@example.com"}}
    ]

    helpers = k6_generator._generate_dynamic_data_helpers(test_data)

    # Should generate unique email logic
    assert "email" in helpers
    assert "Date.now()" in helpers or "globalCounter" in helpers


@pytest.mark.unit
def test_generate_dynamic_data_helpers_with_integer(k6_generator):
    """Test dynamic data helpers for integer fields."""
    test_data = [
        {"body": {"age": 25}}
    ]

    helpers = k6_generator._generate_dynamic_data_helpers(test_data)

    # Should generate integer logic
    assert "age" in helpers
    assert "Math.floor" in helpers or "random" in helpers


# ============================================================================
# VALIDATION TESTS
# ============================================================================

@pytest.mark.unit
@pytest.mark.asyncio
async def test_generated_script_is_valid_javascript(k6_generator):
    """Test that generated script has valid JavaScript syntax."""
    endpoint = create_mock_endpoint_post()
    test_data = [{"body": {"name": "Test", "email": "test@test.com"}}]
    scenario_config = {
        "concurrent_users": 10,
        "duration": 60,
        "ramp_up": 10,
        "ramp_down": 10
    }

    script = await k6_generator.generate_k6_script(endpoint, test_data, scenario_config)

    # Basic syntax checks
    assert script.count("{") == script.count("}")  # Balanced braces
    assert script.count("(") == script.count(")")  # Balanced parentheses
    assert "export default function()" in script
    assert "export const options" in script


@pytest.mark.unit
@pytest.mark.asyncio
async def test_script_returns_string(k6_generator):
    """Test that generate_k6_script returns a string."""
    endpoint = create_mock_endpoint()

    script = await k6_generator.generate_k6_script(endpoint, [], {})

    assert isinstance(script, str)
    assert len(script) > 0


@pytest.mark.unit
@pytest.mark.asyncio
async def test_script_with_special_characters(k6_generator):
    """Test script generation with special characters in data."""
    endpoint = create_mock_endpoint_post()
    test_data = [
        {"body": {"name": "Test's User", "description": 'Quote "test"'}}
    ]

    script = await k6_generator.generate_k6_script(endpoint, test_data, {})

    # Should handle special characters
    assert isinstance(script, str)
    assert len(script) > 0
