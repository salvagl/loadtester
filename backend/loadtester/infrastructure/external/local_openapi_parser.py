"""
Local OpenAPI Parser
Parser for OpenAPI specifications without AI dependencies
"""

import json
import logging
import re
import yaml
from typing import Dict, List, Optional, Union

logger = logging.getLogger(__name__)


class LocalOpenAPIParser:
    """Local OpenAPI parser that doesn't require AI services."""

    def __init__(self):
        """Initialize parser with spec cache."""
        self._parsed_spec_cache = None

    async def validate_spec(self, spec_content: str) -> bool:
        """Validate OpenAPI specification format locally."""
        try:
            parsed_spec = await self.parse_openapi_spec(spec_content)

            # Check for required OpenAPI fields
            if not isinstance(parsed_spec, dict):
                return False

            # Check for OpenAPI version
            openapi_version = parsed_spec.get('openapi') or parsed_spec.get('swagger')
            if not openapi_version:
                return False

            # Check for basic structure
            if 'info' not in parsed_spec:
                return False

            info = parsed_spec.get('info', {})
            if not info.get('title') or not info.get('version'):
                return False

            return True

        except Exception as e:
            logger.error(f"Local validation error: {str(e)}")
            return False

    async def parse_openapi_spec(self, spec_content: str) -> Dict:
        """Parse OpenAPI specification locally."""
        try:
            # First try to parse as JSON
            try:
                parsed = json.loads(spec_content)
                self._parsed_spec_cache = parsed
                return parsed
            except json.JSONDecodeError:
                pass

            # Then try to parse as YAML
            try:
                parsed = yaml.safe_load(spec_content)
                self._parsed_spec_cache = parsed
                return parsed
            except yaml.YAMLError:
                pass

            # If both fail, try to clean the content
            cleaned_content = self._clean_spec_content(spec_content)

            try:
                parsed = json.loads(cleaned_content)
                self._parsed_spec_cache = parsed
                return parsed
            except json.JSONDecodeError:
                pass

            try:
                parsed = yaml.safe_load(cleaned_content)
                self._parsed_spec_cache = parsed
                return parsed
            except yaml.YAMLError:
                pass

            raise ValueError("Unable to parse specification as JSON or YAML")

        except Exception as e:
            logger.error(f"Error parsing OpenAPI spec locally: {str(e)}")
            raise

    async def extract_endpoints(self, parsed_spec: Dict) -> List[Dict]:
        """Extract endpoints from parsed OpenAPI spec locally."""
        try:
            endpoints = []
            paths = parsed_spec.get('paths', {})

            for path, path_data in paths.items():
                if not isinstance(path_data, dict):
                    continue

                for method, operation in path_data.items():
                    # Skip non-HTTP methods
                    if method.upper() not in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS']:
                        continue

                    if not isinstance(operation, dict):
                        continue

                    # Extract endpoint information
                    endpoint = {
                        'path': path,
                        'method': method.upper(),
                        'summary': operation.get('summary', ''),
                        'description': operation.get('description', ''),
                        'parameters': operation.get('parameters', []),
                        'requestBody': operation.get('requestBody', {}),
                        'responses': operation.get('responses', {})
                    }

                    endpoints.append(endpoint)

            logger.info(f"Extracted {len(endpoints)} endpoints locally")
            return endpoints

        except Exception as e:
            logger.error(f"Error extracting endpoints locally: {str(e)}")
            raise

    async def get_endpoint_schema(
        self,
        parsed_spec: Dict,
        path: str,
        method: str
    ) -> Optional[Dict]:
        """Get schema for specific endpoint locally with resolved $refs."""
        try:
            # Cache the spec for reference resolution
            self._parsed_spec_cache = parsed_spec

            paths = parsed_spec.get('paths', {})
            path_data = paths.get(path, {})
            operation = path_data.get(method.lower(), {})

            if not operation:
                return None

            # Extract base schema
            schema = {
                "parameters": operation.get('parameters', []),
                "requestBody": operation.get('requestBody', {}),
                "responses": operation.get('responses', {}),
                "security": operation.get('security', [])
            }

            # Resolve $refs in requestBody
            if schema['requestBody']:
                schema['requestBody'] = self.resolve_schema_refs(schema['requestBody'], parsed_spec)

            # Resolve $refs in parameters
            if schema['parameters']:
                schema['parameters'] = [
                    self.resolve_schema_refs(param, parsed_spec) if isinstance(param, dict) else param
                    for param in schema['parameters']
                ]

            return schema

        except Exception as e:
            logger.error(f"Error getting endpoint schema locally: {str(e)}")
            return None

    def _clean_spec_content(self, spec_content: str) -> str:
        """Clean specification content to handle common formatting issues."""
        # Remove BOM if present
        if spec_content.startswith('\ufeff'):
            spec_content = spec_content[1:]

        # Strip whitespace
        spec_content = spec_content.strip()

        # Remove comments from JSON (basic approach)
        if spec_content.startswith('{'):
            # Remove single-line comments
            spec_content = re.sub(r'//.*', '', spec_content)
            # Remove multi-line comments
            spec_content = re.sub(r'/\*.*?\*/', '', spec_content, flags=re.DOTALL)

        return spec_content

    def get_service_name(self) -> str:
        """Get service name."""
        return "Local OpenAPI Parser"

    def resolve_ref(self, ref: str, spec: Optional[Dict] = None) -> Optional[Dict]:
        """
        Resolve a $ref reference in the OpenAPI spec.

        Args:
            ref: Reference string like '#/components/schemas/Pet'
            spec: OpenAPI spec dict (uses cached spec if not provided)

        Returns:
            Resolved schema dict or None if not found
        """
        if spec is None:
            spec = self._parsed_spec_cache

        if not spec or not ref:
            return None

        # Remove leading '#/' if present
        if ref.startswith('#/'):
            ref = ref[2:]

        # Split the reference path
        path_parts = ref.split('/')

        # Navigate through the spec
        current = spec
        for part in path_parts:
            if not isinstance(current, dict):
                return None
            current = current.get(part)
            if current is None:
                return None

        # If the resolved schema has a $ref, resolve it recursively
        if isinstance(current, dict) and '$ref' in current:
            return self.resolve_ref(current['$ref'], spec)

        return current

    def resolve_schema_refs(self, schema: Dict, spec: Optional[Dict] = None) -> Dict:
        """
        Recursively resolve all $ref references in a schema.

        Args:
            schema: Schema dict that may contain $ref
            spec: OpenAPI spec dict (uses cached spec if not provided)

        Returns:
            Schema with all $refs resolved
        """
        if spec is None:
            spec = self._parsed_spec_cache

        if not isinstance(schema, dict):
            return schema

        # If this is a $ref, resolve it
        if '$ref' in schema:
            ref_path = schema['$ref']
            resolved = self.resolve_ref(ref_path, spec)
            if resolved:
                # Merge other properties from schema (like description overrides)
                resolved_copy = resolved.copy()
                for key, value in schema.items():
                    if key != '$ref':
                        resolved_copy[key] = value
                return self.resolve_schema_refs(resolved_copy, spec)
            return schema

        # Recursively resolve refs in nested objects
        result = {}
        for key, value in schema.items():
            if isinstance(value, dict):
                result[key] = self.resolve_schema_refs(value, spec)
            elif isinstance(value, list):
                result[key] = [
                    self.resolve_schema_refs(item, spec) if isinstance(item, dict) else item
                    for item in value
                ]
            else:
                result[key] = value

        return result