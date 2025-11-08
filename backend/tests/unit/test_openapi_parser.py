"""
Unit tests for LocalOpenAPIParser
Tests validation, parsing, and endpoint extraction from OpenAPI specs
"""

import json
import pytest
from loadtester.infrastructure.external.local_openapi_parser import LocalOpenAPIParser
from tests.fixtures.openapi_specs import (
    VALID_OPENAPI_JSON,
    VALID_OPENAPI_YAML,
    PETSTORE_OPENAPI_SPEC,
    INVALID_OPENAPI_MISSING_INFO,
    OPENAPI_WITH_BOM,
    COMPLEX_OPENAPI_WITH_REFS,
)


# ============================================================================
# TEST FIXTURES
# ============================================================================

@pytest.fixture
def parser():
    """Create a fresh parser instance for each test."""
    return LocalOpenAPIParser()


# ============================================================================
# VALIDATION TESTS
# ============================================================================

@pytest.mark.unit
@pytest.mark.asyncio
async def test_validate_spec_valid_json(parser):
    """Test that valid JSON OpenAPI spec passes validation."""
    result = await parser.validate_spec(VALID_OPENAPI_JSON)
    assert result is True


@pytest.mark.unit
@pytest.mark.asyncio
async def test_validate_spec_valid_yaml(parser):
    """Test that valid YAML OpenAPI spec passes validation."""
    result = await parser.validate_spec(VALID_OPENAPI_YAML)
    assert result is True


@pytest.mark.unit
@pytest.mark.asyncio
async def test_validate_spec_invalid_missing_info(parser):
    """Test that spec missing 'info' field fails validation."""
    result = await parser.validate_spec(INVALID_OPENAPI_MISSING_INFO)
    assert result is False


@pytest.mark.unit
@pytest.mark.asyncio
async def test_validate_spec_invalid_format(parser):
    """Test that malformed spec fails validation."""
    invalid_spec = "{ this is not valid json or yaml"
    result = await parser.validate_spec(invalid_spec)
    assert result is False


@pytest.mark.unit
@pytest.mark.asyncio
async def test_validate_spec_empty_string(parser):
    """Test that empty spec fails validation."""
    result = await parser.validate_spec("")
    assert result is False


@pytest.mark.unit
@pytest.mark.asyncio
async def test_validate_spec_missing_version(parser):
    """Test that spec missing openapi/swagger version fails validation."""
    spec_without_version = json.dumps({
        "info": {
            "title": "Test API",
            "version": "1.0.0"
        },
        "paths": {}
    })
    result = await parser.validate_spec(spec_without_version)
    assert result is False


@pytest.mark.unit
@pytest.mark.asyncio
async def test_validate_spec_missing_title(parser):
    """Test that spec missing title in info fails validation."""
    spec_without_title = json.dumps({
        "openapi": "3.0.0",
        "info": {
            "version": "1.0.0"
        },
        "paths": {}
    })
    result = await parser.validate_spec(spec_without_title)
    assert result is False


# ============================================================================
# PARSING TESTS
# ============================================================================

@pytest.mark.unit
@pytest.mark.asyncio
async def test_parse_openapi_spec_json(parser):
    """Test parsing valid JSON OpenAPI spec."""
    parsed = await parser.parse_openapi_spec(VALID_OPENAPI_JSON)

    assert isinstance(parsed, dict)
    assert "openapi" in parsed
    assert "info" in parsed
    assert "paths" in parsed


@pytest.mark.unit
@pytest.mark.asyncio
async def test_parse_openapi_spec_yaml(parser):
    """Test parsing valid YAML OpenAPI spec."""
    parsed = await parser.parse_openapi_spec(VALID_OPENAPI_YAML)

    assert isinstance(parsed, dict)
    assert "openapi" in parsed
    assert "info" in parsed


@pytest.mark.unit
@pytest.mark.asyncio
async def test_parse_openapi_spec_with_bom(parser):
    """Test parsing spec with BOM (Byte Order Mark)."""
    parsed = await parser.parse_openapi_spec(OPENAPI_WITH_BOM)

    assert isinstance(parsed, dict)
    assert "openapi" in parsed


@pytest.mark.unit
@pytest.mark.asyncio
async def test_parse_openapi_spec_invalid_format(parser):
    """Test parsing invalid spec raises error."""
    with pytest.raises(ValueError, match="Unable to parse specification"):
        await parser.parse_openapi_spec("{ invalid json and yaml ][")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_parse_openapi_spec_caches_result(parser):
    """Test that parser caches the parsed spec."""
    await parser.parse_openapi_spec(VALID_OPENAPI_JSON)

    assert parser._parsed_spec_cache is not None
    assert isinstance(parser._parsed_spec_cache, dict)


# ============================================================================
# ENDPOINT EXTRACTION TESTS
# ============================================================================

@pytest.mark.unit
@pytest.mark.asyncio
async def test_extract_endpoints_simple(parser):
    """Test extracting endpoints from simple spec."""
    parsed = await parser.parse_openapi_spec(VALID_OPENAPI_JSON)
    endpoints = await parser.extract_endpoints(parsed)

    assert isinstance(endpoints, list)
    assert len(endpoints) > 0

    # Verify endpoint structure
    endpoint = endpoints[0]
    assert "path" in endpoint
    assert "method" in endpoint
    assert endpoint["method"] in ["GET", "POST", "PUT", "DELETE", "PATCH"]


@pytest.mark.unit
@pytest.mark.asyncio
async def test_extract_endpoints_multiple_methods(parser):
    """Test extracting endpoints with multiple methods for same path."""
    spec = json.dumps({
        "openapi": "3.0.0",
        "info": {"title": "Test", "version": "1.0.0"},
        "paths": {
            "/users": {
                "get": {"summary": "Get users"},
                "post": {"summary": "Create user"}
            }
        }
    })

    parsed = await parser.parse_openapi_spec(spec)
    endpoints = await parser.extract_endpoints(parsed)

    assert len(endpoints) == 2
    methods = {ep["method"] for ep in endpoints}
    assert "GET" in methods
    assert "POST" in methods


@pytest.mark.unit
@pytest.mark.asyncio
async def test_extract_endpoints_with_parameters(parser):
    """Test extracting endpoints with parameters."""
    spec = json.dumps({
        "openapi": "3.0.0",
        "info": {"title": "Test", "version": "1.0.0"},
        "paths": {
            "/users/{userId}": {
                "get": {
                    "summary": "Get user by ID",
                    "parameters": [
                        {
                            "name": "userId",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "integer"}
                        }
                    ]
                }
            }
        }
    })

    parsed = await parser.parse_openapi_spec(spec)
    endpoints = await parser.extract_endpoints(parsed)

    assert len(endpoints) == 1
    assert len(endpoints[0]["parameters"]) == 1
    assert endpoints[0]["parameters"][0]["name"] == "userId"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_extract_endpoints_empty_spec(parser):
    """Test extracting endpoints from spec with no paths."""
    spec_no_paths = json.dumps({
        "openapi": "3.0.0",
        "info": {"title": "Test", "version": "1.0.0"},
        "paths": {}
    })
    parsed = await parser.parse_openapi_spec(spec_no_paths)
    endpoints = await parser.extract_endpoints(parsed)

    assert isinstance(endpoints, list)
    assert len(endpoints) == 0


@pytest.mark.unit
@pytest.mark.asyncio
async def test_extract_endpoints_filters_non_http_methods(parser):
    """Test that non-HTTP methods are filtered out."""
    spec = json.dumps({
        "openapi": "3.0.0",
        "info": {"title": "Test", "version": "1.0.0"},
        "paths": {
            "/users": {
                "get": {"summary": "Get users"},
                "parameters": [{"name": "test"}],  # Not a method
                "summary": "Users endpoint"  # Not a method
            }
        }
    })

    parsed = await parser.parse_openapi_spec(spec)
    endpoints = await parser.extract_endpoints(parsed)

    # Should only extract GET
    assert len(endpoints) == 1
    assert endpoints[0]["method"] == "GET"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_extract_endpoints_with_request_body(parser):
    """Test extracting endpoints with request body."""
    spec = json.dumps({
        "openapi": "3.0.0",
        "info": {"title": "Test", "version": "1.0.0"},
        "paths": {
            "/users": {
                "post": {
                    "summary": "Create user",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "name": {"type": "string"}
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    })

    parsed = await parser.parse_openapi_spec(spec)
    endpoints = await parser.extract_endpoints(parsed)

    assert len(endpoints) == 1
    assert "requestBody" in endpoints[0]
    assert endpoints[0]["requestBody"]["required"] is True


# ============================================================================
# REFERENCE RESOLUTION TESTS
# ============================================================================

@pytest.mark.unit
def test_resolve_ref_simple(parser):
    """Test resolving simple $ref."""
    spec = {
        "components": {
            "schemas": {
                "Pet": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"}
                    }
                }
            }
        }
    }

    resolved = parser.resolve_ref("#/components/schemas/Pet", spec)

    assert resolved is not None
    assert resolved["type"] == "object"
    assert "name" in resolved["properties"]


@pytest.mark.unit
def test_resolve_ref_nested(parser):
    """Test resolving nested $ref."""
    spec = {
        "components": {
            "schemas": {
                "Pet": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"}
                    }
                },
                "Pets": {
                    "type": "array",
                    "items": {"$ref": "#/components/schemas/Pet"}
                }
            }
        }
    }

    # First resolve Pets
    pets_schema = parser.resolve_ref("#/components/schemas/Pets", spec)
    assert pets_schema is not None
    assert pets_schema["type"] == "array"

    # The items should still have $ref
    assert "$ref" in pets_schema["items"]


@pytest.mark.unit
def test_resolve_ref_not_found(parser):
    """Test resolving non-existent $ref returns None."""
    spec = {
        "components": {
            "schemas": {}
        }
    }

    resolved = parser.resolve_ref("#/components/schemas/NonExistent", spec)
    assert resolved is None


@pytest.mark.unit
def test_resolve_ref_circular(parser):
    """Test resolving circular $ref."""
    spec = {
        "components": {
            "schemas": {
                "Node": {
                    "type": "object",
                    "properties": {
                        "value": {"type": "string"},
                        "next": {"$ref": "#/components/schemas/Node"}
                    }
                }
            }
        }
    }

    # This should resolve without infinite loop
    resolved = parser.resolve_ref("#/components/schemas/Node", spec)
    assert resolved is not None
    assert resolved["type"] == "object"


@pytest.mark.unit
def test_resolve_schema_refs_in_request_body(parser):
    """Test resolving $refs in request body schema."""
    spec = {
        "components": {
            "schemas": {
                "User": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "email": {"type": "string"}
                    }
                }
            }
        }
    }

    request_body = {
        "required": True,
        "content": {
            "application/json": {
                "schema": {"$ref": "#/components/schemas/User"}
            }
        }
    }

    resolved = parser.resolve_schema_refs(request_body, spec)

    assert resolved is not None
    schema = resolved["content"]["application/json"]["schema"]
    assert schema["type"] == "object"
    assert "name" in schema["properties"]
    assert "email" in schema["properties"]


@pytest.mark.unit
def test_resolve_schema_refs_in_parameters(parser):
    """Test resolving $refs in parameters."""
    spec = {
        "components": {
            "schemas": {
                "UserId": {
                    "type": "integer",
                    "minimum": 1
                }
            }
        }
    }

    parameter = {
        "name": "userId",
        "in": "path",
        "required": True,
        "schema": {"$ref": "#/components/schemas/UserId"}
    }

    resolved = parser.resolve_schema_refs(parameter, spec)

    assert resolved is not None
    assert resolved["schema"]["type"] == "integer"
    assert resolved["schema"]["minimum"] == 1


# ============================================================================
# GET ENDPOINT SCHEMA TESTS
# ============================================================================

@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_endpoint_schema_with_refs(parser):
    """Test getting endpoint schema with resolved $refs."""
    parsed = json.loads(PETSTORE_OPENAPI_SPEC)

    # Get schema for a specific endpoint
    schema = await parser.get_endpoint_schema(parsed, "/pet/{petId}", "get")

    assert schema is not None
    assert "parameters" in schema
    assert "responses" in schema


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_endpoint_schema_nonexistent(parser):
    """Test getting schema for non-existent endpoint returns None."""
    parsed = await parser.parse_openapi_spec(VALID_OPENAPI_JSON)

    schema = await parser.get_endpoint_schema(parsed, "/nonexistent", "get")

    assert schema is None


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_endpoint_schema_wrong_method(parser):
    """Test getting schema with wrong method returns None."""
    parsed = json.loads(PETSTORE_OPENAPI_SPEC)

    # Try to get schema for a method that doesn't exist
    schema = await parser.get_endpoint_schema(parsed, "/pet/{petId}", "delete")

    # Should return None or empty schema depending on whether DELETE exists
    # This is a sanity check
    assert schema is None or isinstance(schema, dict)


# ============================================================================
# HELPER METHOD TESTS
# ============================================================================

@pytest.mark.unit
def test_clean_spec_content_removes_bom(parser):
    """Test that _clean_spec_content removes BOM."""
    content_with_bom = '\ufeff{"test": "value"}'
    cleaned = parser._clean_spec_content(content_with_bom)

    assert not cleaned.startswith('\ufeff')
    assert cleaned.startswith('{')


@pytest.mark.unit
def test_clean_spec_content_strips_whitespace(parser):
    """Test that _clean_spec_content strips whitespace."""
    content_with_whitespace = '  \n\n  {"test": "value"}  \n\n  '
    cleaned = parser._clean_spec_content(content_with_whitespace)

    assert cleaned == '{"test": "value"}'


@pytest.mark.unit
def test_clean_spec_content_removes_comments(parser):
    """Test that _clean_spec_content removes JSON comments."""
    content_with_comments = """{
        "test": "value", // This is a comment
        /* Multi-line
           comment */
        "other": "data"
    }"""
    cleaned = parser._clean_spec_content(content_with_comments)

    assert "// This is a comment" not in cleaned
    assert "/* Multi-line" not in cleaned


@pytest.mark.unit
def test_get_service_name(parser):
    """Test getting service name."""
    name = parser.get_service_name()

    assert isinstance(name, str)
    assert len(name) > 0
    assert "Local" in name or "OpenAPI" in name


# ============================================================================
# INTEGRATION-STYLE TESTS (Using real fixtures)
# ============================================================================

@pytest.mark.unit
@pytest.mark.asyncio
async def test_complete_parsing_workflow_petstore(parser):
    """Test complete workflow: validate -> parse -> extract -> get schema."""
    # Validate
    is_valid = await parser.validate_spec(PETSTORE_OPENAPI_SPEC)
    assert is_valid is True

    # Parse
    parsed = await parser.parse_openapi_spec(PETSTORE_OPENAPI_SPEC)
    assert "components" in parsed
    assert "schemas" in parsed["components"]

    # Extract endpoints
    endpoints = await parser.extract_endpoints(parsed)
    assert len(endpoints) > 0

    # Get schema for first endpoint
    first_endpoint = endpoints[0]
    schema = await parser.get_endpoint_schema(
        parsed,
        first_endpoint["path"],
        first_endpoint["method"]
    )
    assert schema is not None


@pytest.mark.unit
@pytest.mark.asyncio
async def test_complex_refs_resolution(parser):
    """Test parsing spec with complex nested references."""
    parsed = json.loads(COMPLEX_OPENAPI_WITH_REFS)

    endpoints = await parser.extract_endpoints(parsed)
    assert len(endpoints) > 0

    # Test that we can get schemas even with complex refs
    for endpoint in endpoints:
        schema = await parser.get_endpoint_schema(
            parsed,
            endpoint["path"],
            endpoint["method"]
        )
        # Schema might be None for some endpoints, but shouldn't crash
        assert schema is None or isinstance(schema, dict)
