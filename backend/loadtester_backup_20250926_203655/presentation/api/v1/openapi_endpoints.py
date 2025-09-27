"""
OpenAPI Endpoints
FastAPI endpoints for OpenAPI specification handling
"""

import logging
from typing import Dict, List

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, validator

from app.infrastructure.config.dependencies import get_openapi_parser_service
from app.infrastructure.external.ai_client import OpenAPIParserService

logger = logging.getLogger(__name__)

router = APIRouter()


# Request/Response Models
class OpenAPISpecRequest(BaseModel):
    """OpenAPI specification request model."""
    spec_content: str = Field(..., description="OpenAPI specification content (JSON/YAML)")
    
    @validator("spec_content")
    def validate_spec_content(cls, v):
        if not v.strip():
            raise ValueError("spec_content cannot be empty")
        return v.strip()


class ValidationResponse(BaseModel):
    """OpenAPI validation response model."""
    valid: bool = Field(..., description="Whether the specification is valid")
    message: str = Field(..., description="Validation message")
    errors: List[str] = Field(default_factory=list, description="List of validation errors")


class EndpointInfo(BaseModel):
    """Endpoint information model."""
    path: str = Field(..., description="Endpoint path")
    method: str = Field(..., description="HTTP method")
    summary: str = Field("", description="Endpoint summary")
    description: str = Field("", description="Endpoint description")
    parameters: List[Dict] = Field(default_factory=list, description="Endpoint parameters")
    request_body: Dict = Field(default_factory=dict, description="Request body schema")
    responses: Dict = Field(default_factory=dict, description="Response schemas")


class ParsedSpecResponse(BaseModel):
    """Parsed OpenAPI specification response model."""
    info: Dict = Field(..., description="API information")
    servers: List[Dict] = Field(default_factory=list, description="Server configurations")
    endpoints: List[EndpointInfo] = Field(default_factory=list, description="Available endpoints")
    total_endpoints: int = Field(..., description="Total number of endpoints")


# API Endpoints
@router.post(
    "/openapi/validate",
    response_model=ValidationResponse,
    summary="Validate OpenAPI Spec",
    description="Validate an OpenAPI specification format and structure"
)
async def validate_openapi_spec(
    request: OpenAPISpecRequest,
    openapi_parser: OpenAPIParserService = Depends(get_openapi_parser_service)
) -> ValidationResponse:
    """Validate OpenAPI specification."""
    try:
        logger.info("Validating OpenAPI specification")
        
        is_valid = await openapi_parser.validate_spec(request.spec_content)
        
        if is_valid:
            return ValidationResponse(
                valid=True,
                message="OpenAPI specification is valid",
                errors=[]
            )
        else:
            return ValidationResponse(
                valid=False,
                message="OpenAPI specification is invalid",
                errors=["Specification format is not valid OpenAPI 3.0+"]
            )
        
    except Exception as e:
        logger.error(f"Error validating OpenAPI spec: {str(e)}")
        return ValidationResponse(
            valid=False,
            message="Error validating specification",
            errors=[str(e)]
        )


@router.post(
    "/openapi/parse",
    response_model=ParsedSpecResponse,
    summary="Parse OpenAPI Spec",
    description="Parse OpenAPI specification and extract endpoint information"
)
async def parse_openapi_spec(
    request: OpenAPISpecRequest,
    openapi_parser: OpenAPIParserService = Depends(get_openapi_parser_service)
) -> ParsedSpecResponse:
    """Parse OpenAPI specification and extract endpoints."""
    try:
        logger.info("Parsing OpenAPI specification")
        
        # First validate the spec
        is_valid = await openapi_parser.validate_spec(request.spec_content)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid OpenAPI specification"
            )
        
        # Parse the specification
        parsed_spec = await openapi_parser.parse_openapi_spec(request.spec_content)
        
        # Extract endpoints
        endpoints_data = await openapi_parser.extract_endpoints(parsed_spec)
        
        # Convert to response format
        endpoints = [
            EndpointInfo(
                path=ep.get("path", ""),
                method=ep.get("method", ""),
                summary=ep.get("summary", ""),
                description=ep.get("description", ""),
                parameters=ep.get("parameters", []),
                request_body=ep.get("requestBody", {}),
                responses=ep.get("responses", {})
            )
            for ep in endpoints_data
        ]
        
        return ParsedSpecResponse(
            info=parsed_spec.get("info", {}),
            servers=parsed_spec.get("servers", []),
            endpoints=endpoints,
            total_endpoints=len(endpoints)
        )
        
    except HTTPException:
        raise
    
    except Exception as e:
        logger.error(f"Error parsing OpenAPI spec: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error parsing specification: {str(e)}"
        )


@router.get(
    "/openapi/endpoint-schema/{path:path}/{method}",
    summary="Get Endpoint Schema",
    description="Get detailed schema for a specific endpoint"
)
async def get_endpoint_schema(
    path: str,
    method: str,
    spec_content: str,
    openapi_parser: OpenAPIParserService = Depends(get_openapi_parser_service)
) -> Dict:
    """Get schema for specific endpoint."""
    try:
        logger.info(f"Getting schema for {method.upper()} {path}")
        
        # Parse the spec first
        parsed_spec = await openapi_parser.parse_openapi_spec(spec_content)
        
        # Get endpoint schema
        schema = await openapi_parser.get_endpoint_schema(parsed_spec, path, method.upper())
        
        if not schema:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Endpoint {method.upper()} {path} not found in specification"
            )
        
        return {
            "path": path,
            "method": method.upper(),
            "schema": schema
        }
        
    except HTTPException:
        raise
    
    except Exception as e:
        logger.error(f"Error getting endpoint schema: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error retrieving endpoint schema: {str(e)}"
        )


@router.post(
    "/openapi/endpoints/filter",
    summary="Filter Endpoints",
    description="Filter endpoints by method, path pattern, or other criteria"
)
async def filter_endpoints(
    request: OpenAPISpecRequest,
    methods: List[str] = None,
    path_pattern: str = None,
    openapi_parser: OpenAPIParserService = Depends(get_openapi_parser_service)
) -> Dict:
    """Filter endpoints based on criteria."""
    try:
        logger.info("Filtering endpoints")
        
        # Parse specification
        parsed_spec = await openapi_parser.parse_openapi_spec(request.spec_content)
        endpoints_data = await openapi_parser.extract_endpoints(parsed_spec)
        
        # Apply filters
        filtered_endpoints = endpoints_data
        
        if methods:
            methods_upper = [m.upper() for m in methods]
            filtered_endpoints = [
                ep for ep in filtered_endpoints 
                if ep.get("method", "").upper() in methods_upper
            ]
        
        if path_pattern:
            filtered_endpoints = [
                ep for ep in filtered_endpoints 
                if path_pattern.lower() in ep.get("path", "").lower()
            ]
        
        return {
            "total_available": len(endpoints_data),
            "total_filtered": len(filtered_endpoints),
            "endpoints": filtered_endpoints,
            "filters_applied": {
                "methods": methods,
                "path_pattern": path_pattern
            }
        }
        
    except Exception as e:
        logger.error(f"Error filtering endpoints: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error filtering endpoints: {str(e)}"
        )