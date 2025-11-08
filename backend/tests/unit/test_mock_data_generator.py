"""
Unit tests for MockDataGeneratorService
Tests data generation from OpenAPI schemas using Faker
"""

import json
import pytest
from unittest.mock import AsyncMock, MagicMock
from loadtester.infrastructure.external.mock_data_service import MockDataGeneratorService
from tests.fixtures.mock_data import create_mock_endpoint, create_mock_endpoint_post


# ============================================================================
# TEST FIXTURES
# ============================================================================

@pytest.fixture
def mock_ai_client():
    """Create a mock AI client."""
    client = MagicMock()
    client.chat_completion = AsyncMock(return_value='[{"name": "Test User", "email": "test@example.com"}]')
    return client


@pytest.fixture
def generator(mock_ai_client):
    """Create a MockDataGeneratorService instance with mocked AI client."""
    return MockDataGeneratorService(ai_client=mock_ai_client)


# ============================================================================
# FAKER VALUE GENERATION TESTS
# ============================================================================

@pytest.mark.unit
def test_generate_faker_value_integer(generator):
    """Test generating integer values."""
    value = generator._generate_faker_value("integer", "userId")

    assert isinstance(value, int)
    assert 1 <= value <= 10000


@pytest.mark.unit
def test_generate_faker_value_email(generator):
    """Test generating unique email values."""
    email1 = generator._generate_faker_value("email", "userEmail")
    email2 = generator._generate_faker_value("email", "userEmail")

    assert isinstance(email1, str)
    assert "@" in email1
    assert "." in email1
    # Emails should be unique
    assert email1 != email2


@pytest.mark.unit
def test_generate_faker_value_phone(generator):
    """Test generating phone number values."""
    value = generator._generate_faker_value("phone", "phoneNumber")

    assert isinstance(value, str)
    assert len(value) > 0


@pytest.mark.unit
def test_generate_faker_value_date(generator):
    """Test generating date values."""
    value = generator._generate_faker_value("date", "birthDate")

    assert isinstance(value, str)
    # Should be ISO format
    assert "-" in value


@pytest.mark.unit
def test_generate_faker_value_url(generator):
    """Test generating URL values."""
    value = generator._generate_faker_value("url", "websiteUrl")

    assert isinstance(value, str)
    assert value.startswith("http")


@pytest.mark.unit
def test_generate_faker_value_name_variations(generator):
    """Test generating different name types."""
    # Full name
    full_name = generator._generate_faker_value("string", "name")
    assert isinstance(full_name, str)
    assert len(full_name.split()) >= 2  # Should have first and last name

    # First name
    first_name = generator._generate_faker_value("string", "firstName")
    assert isinstance(first_name, str)

    # Last name
    last_name = generator._generate_faker_value("string", "apellido")
    assert isinstance(last_name, str)


@pytest.mark.unit
def test_generate_faker_value_address(generator):
    """Test generating address values."""
    value = generator._generate_faker_value("string", "address")

    assert isinstance(value, str)
    assert len(value) > 0


@pytest.mark.unit
def test_generate_faker_value_company(generator):
    """Test generating company name values."""
    value = generator._generate_faker_value("string", "company")

    assert isinstance(value, str)
    assert len(value) > 0


@pytest.mark.unit
def test_generate_faker_value_uuid_from_schema_format(generator):
    """Test generating UUID values from schema format (not from name)."""
    # When using schema with format="uuid", use _generate_value_from_property_schema
    prop_schema = {"type": "string", "format": "uuid"}
    value = generator._generate_value_from_property_schema("correlationId", prop_schema)

    assert isinstance(value, str)
    assert len(value) == 36  # UUID format
    assert value.count("-") == 4  # UUID has 4 hyphens


# ============================================================================
# SCHEMA-BASED GENERATION TESTS
# ============================================================================

@pytest.mark.unit
def test_generate_body_from_schema_simple_object(generator):
    """Test generating body from simple object schema."""
    schema = {
        "type": "object",
        "required": ["name", "email"],
        "properties": {
            "name": {"type": "string"},
            "email": {"type": "string", "format": "email"}
        }
    }

    body = generator._generate_body_from_schema(schema)

    assert isinstance(body, dict)
    assert "name" in body
    assert "email" in body
    assert "@" in body["email"]


@pytest.mark.unit
def test_generate_body_from_schema_nested_object(generator):
    """Test generating body from nested object schema."""
    schema = {
        "type": "object",
        "required": ["user"],
        "properties": {
            "user": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "age": {"type": "integer"}
                }
            }
        }
    }

    body = generator._generate_body_from_schema(schema)

    assert isinstance(body, dict)
    assert "user" in body
    assert isinstance(body["user"], dict)


@pytest.mark.unit
def test_generate_body_from_schema_array(generator):
    """Test generating body from array schema."""
    schema = {
        "type": "array",
        "items": {
            "type": "string"
        }
    }

    body = generator._generate_body_from_schema(schema)

    assert isinstance(body, list)
    assert len(body) > 0
    assert all(isinstance(item, str) for item in body)


@pytest.mark.unit
def test_generate_body_from_schema_with_required_fields(generator):
    """Test that required fields are always generated."""
    schema = {
        "type": "object",
        "required": ["id", "name", "email"],
        "properties": {
            "id": {"type": "integer"},
            "name": {"type": "string"},
            "email": {"type": "string", "format": "email"},
            "age": {"type": "integer"}  # Optional
        }
    }

    # Generate multiple times to verify required fields always present
    for _ in range(5):
        body = generator._generate_body_from_schema(schema)

        # Required fields must always be present
        assert "id" in body
        assert "name" in body
        assert "email" in body
        # Optional field may or may not be present


@pytest.mark.unit
def test_generate_body_from_schema_with_enums(generator):
    """Test generating values from enum."""
    schema = {
        "type": "object",
        "required": ["status"],
        "properties": {
            "status": {
                "type": "string",
                "enum": ["active", "inactive", "pending"]
            }
        }
    }

    body = generator._generate_body_from_schema(schema)

    assert "status" in body
    assert body["status"] in ["active", "inactive", "pending"]


@pytest.mark.unit
def test_generate_body_from_schema_empty(generator):
    """Test generating from empty schema."""
    body = generator._generate_body_from_schema({})

    assert isinstance(body, dict)


@pytest.mark.unit
def test_generate_body_from_schema_with_integer_constraints(generator):
    """Test generating integers with min/max constraints."""
    schema = {
        "type": "object",
        "required": ["age"],
        "properties": {
            "age": {
                "type": "integer",
                "minimum": 18,
                "maximum": 65
            }
        }
    }

    body = generator._generate_body_from_schema(schema)

    assert "age" in body
    assert 18 <= body["age"] <= 65


@pytest.mark.unit
def test_generate_body_from_schema_with_number(generator):
    """Test generating number (float) values."""
    schema = {
        "type": "object",
        "required": ["price"],
        "properties": {
            "price": {
                "type": "number",
                "minimum": 0,
                "maximum": 100
            }
        }
    }

    body = generator._generate_body_from_schema(schema)

    assert "price" in body
    assert isinstance(body["price"], (int, float))
    assert 0 <= body["price"] <= 100


@pytest.mark.unit
def test_generate_body_from_schema_with_boolean(generator):
    """Test generating boolean values."""
    schema = {
        "type": "object",
        "required": ["active"],
        "properties": {
            "active": {"type": "boolean"}
        }
    }

    body = generator._generate_body_from_schema(schema)

    assert "active" in body
    assert isinstance(body["active"], bool)


# ============================================================================
# ENDPOINT ANALYSIS TESTS
# ============================================================================

@pytest.mark.unit
@pytest.mark.asyncio
async def test_analyze_endpoint_requirements_path_params(generator):
    """Test analyzing endpoint with path parameters."""
    endpoint = create_mock_endpoint(
        endpoint_path="/users/{userId}/posts/{postId}",
        http_method="GET"
    )

    schema = {}

    data_template = await generator._analyze_endpoint_requirements(endpoint, schema)

    assert "path_params" in data_template
    assert "userId" in data_template["path_params"]
    assert "postId" in data_template["path_params"]


@pytest.mark.unit
@pytest.mark.asyncio
async def test_analyze_endpoint_requirements_query_params(generator):
    """Test analyzing endpoint with query parameters."""
    endpoint = create_mock_endpoint(
        endpoint_path="/users",
        http_method="GET"
    )

    schema = {
        "parameters": [
            {"name": "page", "in": "query", "schema": {"type": "integer"}},
            {"name": "limit", "in": "query", "schema": {"type": "integer"}}
        ]
    }

    data_template = await generator._analyze_endpoint_requirements(endpoint, schema)

    assert "query_params" in data_template
    assert "page" in data_template["query_params"]
    assert "limit" in data_template["query_params"]


@pytest.mark.unit
@pytest.mark.asyncio
async def test_analyze_endpoint_requirements_request_body(generator):
    """Test analyzing endpoint with request body."""
    endpoint = create_mock_endpoint_post()

    schema = {
        "requestBody": {
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "email": {"type": "string"}
                        }
                    }
                }
            }
        }
    }

    data_template = await generator._analyze_endpoint_requirements(endpoint, schema)

    assert "body" in data_template
    assert data_template["body"] is not None
    assert "properties" in data_template["body"]


# ============================================================================
# MOCK DATA GENERATION TESTS
# ============================================================================

@pytest.mark.unit
@pytest.mark.asyncio
async def test_generate_mock_data_count(generator):
    """Test generating specified count of mock data records."""
    endpoint = create_mock_endpoint()
    schema = {}
    count = 50

    mock_data = await generator.generate_mock_data(endpoint, schema, count)

    assert isinstance(mock_data, list)
    assert len(mock_data) == count


@pytest.mark.unit
@pytest.mark.asyncio
async def test_generate_mock_data_unique_emails(generator):
    """Test that generated emails are unique."""
    endpoint = create_mock_endpoint_post()

    schema = {
        "requestBody": {
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "required": ["email"],
                        "properties": {
                            "email": {"type": "string", "format": "email"}
                        }
                    }
                }
            }
        }
    }

    mock_data = await generator.generate_mock_data(endpoint, schema, 100)

    # Extract all emails
    emails = [record.get("body", {}).get("email") for record in mock_data]
    emails = [e for e in emails if e]  # Filter None values

    # Check uniqueness
    assert len(emails) == len(set(emails)), "Emails should be unique"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_generate_mock_data_for_post_endpoint(generator):
    """Test generating data for POST endpoint."""
    endpoint = create_mock_endpoint_post()

    schema = {
        "requestBody": {
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "required": ["name", "email"],
                        "properties": {
                            "name": {"type": "string"},
                            "email": {"type": "string", "format": "email"}
                        }
                    }
                }
            }
        }
    }

    mock_data = await generator.generate_mock_data(endpoint, schema, 10)

    assert len(mock_data) == 10

    # All records should have body
    for record in mock_data:
        assert "body" in record
        assert "name" in record["body"]
        assert "email" in record["body"]


@pytest.mark.unit
@pytest.mark.asyncio
async def test_generate_mock_data_for_get_endpoint(generator):
    """Test generating data for GET endpoint with path params."""
    endpoint = create_mock_endpoint(
        endpoint_path="/users/{userId}",
        http_method="GET"
    )

    schema = {}

    mock_data = await generator.generate_mock_data(endpoint, schema, 10)

    assert len(mock_data) == 10

    # All records should have path_params
    for record in mock_data:
        assert "path_params" in record
        assert "userId" in record["path_params"]


@pytest.mark.unit
@pytest.mark.asyncio
async def test_generate_mock_data_handles_errors_gracefully(generator):
    """Test that generation handles errors gracefully."""
    endpoint = create_mock_endpoint()

    # Invalid schema that might cause issues
    schema = None

    mock_data = await generator.generate_mock_data(endpoint, schema, 10)

    # Should return list, even if empty or with basic data
    assert isinstance(mock_data, list)


# ============================================================================
# HELPER METHODS TESTS
# ============================================================================

@pytest.mark.unit
def test_get_param_type_id(generator):
    """Test inferring parameter type for ID fields."""
    param_type = generator._get_param_type("userId")
    assert param_type == "integer"

    param_type = generator._get_param_type("id")
    assert param_type == "integer"


@pytest.mark.unit
def test_get_param_type_email(generator):
    """Test inferring parameter type for email fields."""
    param_type = generator._get_param_type("userEmail")
    assert param_type == "email"


@pytest.mark.unit
def test_get_param_type_date(generator):
    """Test inferring parameter type for date fields."""
    param_type = generator._get_param_type("birthDate")
    assert param_type == "date"


@pytest.mark.unit
def test_get_param_type_phone(generator):
    """Test inferring parameter type for phone fields."""
    param_type = generator._get_param_type("phoneNumber")
    assert param_type == "phone"


@pytest.mark.unit
def test_get_param_type_url(generator):
    """Test inferring parameter type for URL fields."""
    param_type = generator._get_param_type("websiteUrl")
    assert param_type == "url"


@pytest.mark.unit
def test_get_param_type_default(generator):
    """Test inferring parameter type defaults to string."""
    param_type = generator._get_param_type("randomField")
    assert param_type == "string"


# ============================================================================
# PATH/QUERY PARAMETER GENERATION TESTS
# ============================================================================

@pytest.mark.unit
@pytest.mark.asyncio
async def test_generate_path_parameters(generator):
    """Test generating path parameters from path string."""
    path = "/users/{userId}/posts/{postId}"
    schema = {}

    path_params = await generator.generate_path_parameters(path, schema)

    assert "userId" in path_params
    assert "postId" in path_params
    assert isinstance(path_params["userId"], int)
    assert isinstance(path_params["postId"], int)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_generate_query_parameters(generator):
    """Test generating query parameters from schema."""
    schema = {
        "parameters": [
            {"name": "page", "in": "query", "schema": {"type": "integer"}},
            {"name": "search", "in": "query", "schema": {"type": "string"}}
        ]
    }

    query_params = await generator.generate_query_parameters(schema)

    # Should include schema params
    assert "page" in query_params
    assert "search" in query_params

    # Should also include common params
    assert "limit" in query_params


@pytest.mark.unit
@pytest.mark.asyncio
async def test_generate_request_body(generator):
    """Test generating request body from schema."""
    schema = {
        "type": "object",
        "required": ["name"],
        "properties": {
            "name": {"type": "string"},
            "age": {"type": "integer"}
        }
    }

    body = await generator.generate_request_body(schema)

    assert isinstance(body, dict)
    assert "name" in body


# ============================================================================
# VALIDATION TESTS
# ============================================================================

@pytest.mark.unit
@pytest.mark.asyncio
async def test_validate_generated_data_valid(generator):
    """Test validating valid generated data."""
    data = {"name": "Test User", "email": "test@example.com"}
    schema = {}

    is_valid = await generator.validate_generated_data(data, schema)

    assert is_valid is True


@pytest.mark.unit
@pytest.mark.asyncio
async def test_validate_generated_data_empty(generator):
    """Test validating empty data."""
    data = {}
    schema = {}

    is_valid = await generator.validate_generated_data(data, schema)

    assert is_valid is False


@pytest.mark.unit
@pytest.mark.asyncio
async def test_validate_generated_data_none(generator):
    """Test validating None data."""
    data = None
    schema = {}

    is_valid = await generator.validate_generated_data(data, schema)

    assert is_valid is False


# ============================================================================
# COMPLEX SCENARIO TESTS
# ============================================================================

@pytest.mark.unit
def test_generate_value_from_property_schema_complex(generator):
    """Test generating value from complex property schema."""
    # Array of objects
    prop_schema = {
        "type": "array",
        "items": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "value": {"type": "integer"}
            }
        }
    }

    value = generator._generate_value_from_property_schema("tags", prop_schema)

    assert isinstance(value, list)
    assert len(value) > 0
    for item in value:
        assert isinstance(item, dict)


@pytest.mark.unit
def test_generate_body_from_schema_photo_urls(generator):
    """Test generating array of URLs (like photoUrls in Petstore)."""
    schema = {
        "type": "object",
        "required": ["photoUrls"],
        "properties": {
            "photoUrls": {
                "type": "array",
                "items": {
                    "type": "string",
                    "format": "uri"
                }
            }
        }
    }

    body = generator._generate_body_from_schema(schema)

    assert "photoUrls" in body
    assert isinstance(body["photoUrls"], list)
    assert len(body["photoUrls"]) > 0
    # All items should be URLs
    for url in body["photoUrls"]:
        assert isinstance(url, str)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_generate_mock_data_complex_nested_structure(generator):
    """Test generating data with deeply nested structure."""
    endpoint = create_mock_endpoint_post()

    schema = {
        "requestBody": {
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "required": ["user"],
                        "properties": {
                            "user": {
                                "type": "object",
                                "properties": {
                                    "name": {"type": "string"},
                                    "address": {
                                        "type": "object",
                                        "properties": {
                                            "street": {"type": "string"},
                                            "city": {"type": "string"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    mock_data = await generator.generate_mock_data(endpoint, schema, 5)

    assert len(mock_data) == 5
    for record in mock_data:
        assert "body" in record
        assert "user" in record["body"]
        # Nested address might be optional, but if present should be object
        if "address" in record["body"]["user"]:
            assert isinstance(record["body"]["user"]["address"], dict)
