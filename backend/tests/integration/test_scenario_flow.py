"""
Integration tests for Scenario Generation Flow
Tests complete flow: Endpoint → Mock data generation → Create 6 scenarios → Persist
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from loadtester.domain.services.load_test_service import LoadTestService
from loadtester.infrastructure.repositories.api_repository import APIRepository
from loadtester.infrastructure.repositories.endpoint_repository import EndpointRepository
from loadtester.infrastructure.repositories.test_scenario_repository import TestScenarioRepository
from loadtester.infrastructure.external.mock_data_service import MockDataGeneratorService
from loadtester.domain.entities.domain_entities import API, Endpoint
from tests.fixtures.mock_data import (
    create_mock_endpoint,
    create_mock_endpoint_post,
    create_mock_api
)
from datetime import datetime


# ============================================================================
# INTEGRATION TEST: Complete Scenario Generation Flow
# ============================================================================

@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.requires_db
async def test_complete_scenario_generation_flow(db_session, mock_ai_client):
    """
    Test complete flow: Endpoint → Generate mock data → Create 6 incremental scenarios → Persist all
    """
    # Step 1: Set up repositories and services
    api_repo = APIRepository(db_session)
    endpoint_repo = EndpointRepository(db_session)
    scenario_repo = TestScenarioRepository(db_session)
    mock_generator = MockDataGeneratorService(ai_client=mock_ai_client)

    # Step 2: Create API and Endpoint
    api = create_mock_api(api_name="Scenario Test API", base_url="https://test.com")
    created_api = await api_repo.create(api)

    endpoint = create_mock_endpoint_post(
        api_id=created_api.api_id,
        endpoint_path="/users",
        http_method="POST"
    )
    created_endpoint = await endpoint_repo.create(endpoint)

    # Step 3: Generate mock data
    endpoint_schema = {
        "parameters": [],
        "requestBody": {
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "email": {"type": "string", "format": "email"}
                        },
                        "required": ["name", "email"]
                    }
                }
            }
        }
    }

    mock_data = await mock_generator.generate_mock_data(
        endpoint=created_endpoint,
        endpoint_schema=endpoint_schema,
        count=100
    )

    # Step 4: Generate incremental scenarios (25%, 50%, 75%, 100%, 150%, 200%)
    base_volumetry = 100
    base_users = 10
    percentages = [25, 50, 75, 100, 150, 200]
    scenarios = []

    for i, percentage in enumerate(percentages):
        target_volumetry = max(1, int(base_volumetry * percentage / 100))
        concurrent_users = max(1, int(base_users * percentage / 100))

        is_warmup = (i == 0)  # First scenario is warmup

        scenario = Endpoint(
            endpoint_id=created_endpoint.endpoint_id,
            api_id=created_api.api_id,
            endpoint_path=created_endpoint.endpoint_path,
            http_method=created_endpoint.http_method,
            expected_volumetry=target_volumetry,
            expected_concurrent_users=concurrent_users,
            created_at=datetime.utcnow()
        )

        # Create test scenario entity
        from loadtester.domain.entities.domain_entities import TestScenario
        test_scenario = TestScenario(
            endpoint_id=created_endpoint.endpoint_id,
            scenario_name=f"Scenario {percentage}% - {concurrent_users} users",
            description="Warmup scenario" if is_warmup else f"Load test at {percentage}%",
            target_volumetry=target_volumetry,
            concurrent_users=concurrent_users,
            duration_seconds=60,
            ramp_up_seconds=10,
            ramp_down_seconds=10,
            test_data=mock_data[:target_volumetry] if mock_data else [],
            created_at=datetime.utcnow()
        )

        created_scenario = await scenario_repo.create(test_scenario)
        scenarios.append(created_scenario)

    # Step 5: Verify 6 scenarios were created
    assert len(scenarios) == 6

    # Step 6: Verify scenarios are incremental
    for i in range(len(scenarios) - 1):
        current = scenarios[i]
        next_scenario = scenarios[i + 1]
        assert next_scenario.target_volumetry >= current.target_volumetry
        assert next_scenario.concurrent_users >= current.concurrent_users

    # Step 7: Retrieve scenarios from database
    retrieved_scenarios = await scenario_repo.get_by_endpoint_id(created_endpoint.endpoint_id)
    assert len(retrieved_scenarios) == 6


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.requires_db
async def test_scenario_generation_with_custom_data(db_session, mock_ai_client):
    """Test scenario generation with custom test data."""
    api_repo = APIRepository(db_session)
    endpoint_repo = EndpointRepository(db_session)
    scenario_repo = TestScenarioRepository(db_session)
    mock_generator = MockDataGeneratorService(ai_client=mock_ai_client)

    # Create API and endpoint
    api = create_mock_api()
    created_api = await api_repo.create(api)

    endpoint = create_mock_endpoint_post(api_id=created_api.api_id)
    created_endpoint = await endpoint_repo.create(endpoint)

    # Generate custom mock data
    custom_schema = {
        "parameters": [],
        "requestBody": {
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "userId": {"type": "integer"},
                            "productId": {"type": "integer"},
                            "quantity": {"type": "integer", "minimum": 1, "maximum": 10}
                        }
                    }
                }
            }
        }
    }

    mock_data = await mock_generator.generate_mock_data(
        endpoint=created_endpoint,
        endpoint_schema=custom_schema,
        count=50
    )

    # Create scenario with this data
    from loadtester.domain.entities.domain_entities import TestScenario
    scenario = TestScenario(
        endpoint_id=created_endpoint.endpoint_id,
        scenario_name="Custom Data Scenario",
        target_volumetry=50,
        concurrent_users=5,
        duration_seconds=60,
        test_data=mock_data,
        created_at=datetime.utcnow()
    )

    created_scenario = await scenario_repo.create(scenario)

    # Verify scenario has test data
    assert created_scenario.test_data is not None
    assert len(created_scenario.test_data) == 50


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.requires_db
async def test_scenario_generation_multiple_endpoints(db_session, mock_ai_client):
    """Test creating scenarios for multiple endpoints."""
    api_repo = APIRepository(db_session)
    endpoint_repo = EndpointRepository(db_session)
    scenario_repo = TestScenarioRepository(db_session)

    # Create API
    api = create_mock_api()
    created_api = await api_repo.create(api)

    # Create 3 endpoints
    endpoints = []
    for i in range(3):
        endpoint = create_mock_endpoint(
            api_id=created_api.api_id,
            endpoint_path=f"/endpoint{i}",
            http_method="GET"
        )
        created_endpoint = await endpoint_repo.create(endpoint)
        endpoints.append(created_endpoint)

    # Create 2 scenarios for each endpoint
    from loadtester.domain.entities.domain_entities import TestScenario
    for endpoint in endpoints:
        for j in range(2):
            scenario = TestScenario(
                endpoint_id=endpoint.endpoint_id,
                scenario_name=f"Scenario {j + 1}",
                target_volumetry=50 * (j + 1),
                concurrent_users=5 * (j + 1),
                duration_seconds=60,
                created_at=datetime.utcnow()
            )
            await scenario_repo.create(scenario)

    # Verify each endpoint has 2 scenarios
    for endpoint in endpoints:
        scenarios = await scenario_repo.get_by_endpoint_id(endpoint.endpoint_id)
        assert len(scenarios) == 2


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.requires_db
async def test_scenario_mock_data_sufficient_count(db_session, mock_ai_client):
    """Test that sufficient mock data is generated for scenarios."""
    api_repo = APIRepository(db_session)
    endpoint_repo = EndpointRepository(db_session)
    scenario_repo = TestScenarioRepository(db_session)
    mock_generator = MockDataGeneratorService(ai_client=mock_ai_client)

    # Create API and endpoint
    api = create_mock_api()
    created_api = await api_repo.create(api)

    endpoint = create_mock_endpoint_post(api_id=created_api.api_id)
    created_endpoint = await endpoint_repo.create(endpoint)

    # Generate enough mock data for highest scenario (200%)
    schema = {
        "parameters": [],
        "requestBody": {
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "data": {"type": "string"}
                        }
                    }
                }
            }
        }
    }

    target_volumetry = 100
    # Generate 200% of target (for 200% scenario)
    mock_data = await mock_generator.generate_mock_data(
        endpoint=created_endpoint,
        endpoint_schema=schema,
        count=target_volumetry * 2
    )

    # Verify sufficient data generated
    assert len(mock_data) == target_volumetry * 2

    # Create 200% scenario
    from loadtester.domain.entities.domain_entities import TestScenario
    scenario = TestScenario(
        endpoint_id=created_endpoint.endpoint_id,
        scenario_name="200% Load Scenario",
        target_volumetry=target_volumetry * 2,
        concurrent_users=20,
        duration_seconds=60,
        test_data=mock_data,
        created_at=datetime.utcnow()
    )

    created_scenario = await scenario_repo.create(scenario)

    # Verify scenario has all the data
    assert len(created_scenario.test_data) == target_volumetry * 2


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.requires_db
async def test_scenario_data_uniqueness(db_session, mock_ai_client):
    """Test that generated mock data has unique values (especially emails)."""
    mock_generator = MockDataGeneratorService(ai_client=mock_ai_client)

    endpoint = create_mock_endpoint_post()
    schema = {
        "parameters": [],
        "requestBody": {
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "email": {"type": "string", "format": "email"},
                            "name": {"type": "string"}
                        }
                    }
                }
            }
        }
    }

    # Generate 50 records
    mock_data = await mock_generator.generate_mock_data(
        endpoint=endpoint,
        endpoint_schema=schema,
        count=50
    )

    # Extract emails
    emails = []
    for item in mock_data:
        if 'body' in item and 'email' in item['body']:
            emails.append(item['body']['email'])

    # Verify uniqueness (should have timestamps making them unique)
    unique_emails = set(emails)

    # At least most emails should be unique (allowing for some faker randomness)
    assert len(unique_emails) >= len(emails) * 0.9


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.requires_db
async def test_scenario_with_warmup_flag(db_session):
    """Test creating scenarios with warmup flag."""
    api_repo = APIRepository(db_session)
    endpoint_repo = EndpointRepository(db_session)
    scenario_repo = TestScenarioRepository(db_session)

    # Create API and endpoint
    api = create_mock_api()
    created_api = await api_repo.create(api)

    endpoint = create_mock_endpoint(api_id=created_api.api_id)
    created_endpoint = await endpoint_repo.create(endpoint)

    # Create warmup scenario (25% load)
    from loadtester.domain.entities.domain_entities import TestScenario
    warmup_scenario = TestScenario(
        endpoint_id=created_endpoint.endpoint_id,
        scenario_name="Warmup - 25% Load",
        description="Warmup scenario",
        target_volumetry=25,
        concurrent_users=3,
        duration_seconds=60,
        created_at=datetime.utcnow()
    )

    created_warmup = await scenario_repo.create(warmup_scenario)

    # Verify warmup scenario characteristics
    assert "warmup" in created_warmup.description.lower() or "warmup" in created_warmup.scenario_name.lower()
    assert created_warmup.target_volumetry < 50  # Low load


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.requires_db
async def test_scenario_duration_configuration(db_session):
    """Test scenarios with different duration configurations."""
    api_repo = APIRepository(db_session)
    endpoint_repo = EndpointRepository(db_session)
    scenario_repo = TestScenarioRepository(db_session)

    # Create API and endpoint
    api = create_mock_api()
    created_api = await api_repo.create(api)

    endpoint = create_mock_endpoint(api_id=created_api.api_id)
    created_endpoint = await endpoint_repo.create(endpoint)

    # Create scenarios with different durations
    from loadtester.domain.entities.domain_entities import TestScenario
    durations = [30, 60, 120, 300]  # 30s, 1m, 2m, 5m

    for duration in durations:
        scenario = TestScenario(
            endpoint_id=created_endpoint.endpoint_id,
            scenario_name=f"Scenario {duration}s",
            target_volumetry=100,
            concurrent_users=10,
            duration_seconds=duration,
            ramp_up_seconds=10,
            ramp_down_seconds=10,
            created_at=datetime.utcnow()
        )
        await scenario_repo.create(scenario)

    # Verify all scenarios created
    scenarios = await scenario_repo.get_by_endpoint_id(created_endpoint.endpoint_id)
    assert len(scenarios) == len(durations)

    # Verify durations
    scenario_durations = [s.duration_seconds for s in scenarios]
    assert set(scenario_durations) == set(durations)


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.requires_db
async def test_scenario_ramp_configuration(db_session):
    """Test scenarios with ramp-up and ramp-down configuration."""
    api_repo = APIRepository(db_session)
    endpoint_repo = EndpointRepository(db_session)
    scenario_repo = TestScenarioRepository(db_session)

    # Create API and endpoint
    api = create_mock_api()
    created_api = await api_repo.create(api)

    endpoint = create_mock_endpoint(api_id=created_api.api_id)
    created_endpoint = await endpoint_repo.create(endpoint)

    # Create scenario with specific ramp configuration
    from loadtester.domain.entities.domain_entities import TestScenario
    scenario = TestScenario(
        endpoint_id=created_endpoint.endpoint_id,
        scenario_name="Ramp Test",
        target_volumetry=100,
        concurrent_users=10,
        duration_seconds=60,
        ramp_up_seconds=15,  # 15s ramp-up
        ramp_down_seconds=5,  # 5s ramp-down
        created_at=datetime.utcnow()
    )

    created_scenario = await scenario_repo.create(scenario)

    # Verify ramp configuration
    assert created_scenario.ramp_up_seconds == 15
    assert created_scenario.ramp_down_seconds == 5
    assert created_scenario.duration_seconds == 60


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.requires_db
async def test_scenario_update(db_session):
    """Test updating scenario after creation."""
    api_repo = APIRepository(db_session)
    endpoint_repo = EndpointRepository(db_session)
    scenario_repo = TestScenarioRepository(db_session)

    # Create API and endpoint
    api = create_mock_api()
    created_api = await api_repo.create(api)

    endpoint = create_mock_endpoint(api_id=created_api.api_id)
    created_endpoint = await endpoint_repo.create(endpoint)

    # Create scenario
    from loadtester.domain.entities.domain_entities import TestScenario
    scenario = TestScenario(
        endpoint_id=created_endpoint.endpoint_id,
        scenario_name="Original Name",
        target_volumetry=100,
        concurrent_users=10,
        duration_seconds=60,
        created_at=datetime.utcnow()
    )

    created_scenario = await scenario_repo.create(scenario)

    # Update scenario
    created_scenario.scenario_name = "Updated Name"
    created_scenario.target_volumetry = 150
    updated_scenario = await scenario_repo.update(created_scenario)

    # Verify updates
    assert updated_scenario.scenario_name == "Updated Name"
    assert updated_scenario.target_volumetry == 150


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.requires_db
async def test_scenario_with_minimal_load(db_session):
    """Test scenario with very low load (edge case)."""
    api_repo = APIRepository(db_session)
    endpoint_repo = EndpointRepository(db_session)
    scenario_repo = TestScenarioRepository(db_session)

    # Create API and endpoint
    api = create_mock_api()
    created_api = await api_repo.create(api)

    endpoint = create_mock_endpoint(api_id=created_api.api_id)
    created_endpoint = await endpoint_repo.create(endpoint)

    # Create minimal load scenario
    from loadtester.domain.entities.domain_entities import TestScenario
    scenario = TestScenario(
        endpoint_id=created_endpoint.endpoint_id,
        scenario_name="Minimal Load",
        target_volumetry=1,  # Just 1 request
        concurrent_users=1,  # 1 user
        duration_seconds=10,  # 10 seconds
        ramp_up_seconds=0,
        ramp_down_seconds=0,
        created_at=datetime.utcnow()
    )

    created_scenario = await scenario_repo.create(scenario)

    # Verify minimal values handled correctly
    assert created_scenario.target_volumetry == 1
    assert created_scenario.concurrent_users == 1


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.requires_db
async def test_scenario_with_high_load(db_session):
    """Test scenario with very high load (stress test)."""
    api_repo = APIRepository(db_session)
    endpoint_repo = EndpointRepository(db_session)
    scenario_repo = TestScenarioRepository(db_session)

    # Create API and endpoint
    api = create_mock_api()
    created_api = await api_repo.create(api)

    endpoint = create_mock_endpoint(api_id=created_api.api_id)
    created_endpoint = await endpoint_repo.create(endpoint)

    # Create high load scenario
    from loadtester.domain.entities.domain_entities import TestScenario
    scenario = TestScenario(
        endpoint_id=created_endpoint.endpoint_id,
        scenario_name="High Load - 200%",
        target_volumetry=10000,  # 10k requests
        concurrent_users=500,  # 500 concurrent users
        duration_seconds=300,  # 5 minutes
        ramp_up_seconds=30,
        ramp_down_seconds=30,
        created_at=datetime.utcnow()
    )

    created_scenario = await scenario_repo.create(scenario)

    # Verify high load values
    assert created_scenario.target_volumetry == 10000
    assert created_scenario.concurrent_users == 500
