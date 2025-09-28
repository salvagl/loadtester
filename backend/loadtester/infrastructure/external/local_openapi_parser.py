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
                return json.loads(spec_content)
            except json.JSONDecodeError:
                pass

            # Then try to parse as YAML
            try:
                return yaml.safe_load(spec_content)
            except yaml.YAMLError:
                pass

            # If both fail, try to clean the content
            cleaned_content = self._clean_spec_content(spec_content)

            try:
                return json.loads(cleaned_content)
            except json.JSONDecodeError:
                pass

            try:
                return yaml.safe_load(cleaned_content)
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
        """Get schema for specific endpoint locally."""
        try:
            paths = parsed_spec.get('paths', {})
            path_data = paths.get(path, {})
            operation = path_data.get(method.lower(), {})

            if not operation:
                return None

            return {
                "parameters": operation.get('parameters', []),
                "requestBody": operation.get('requestBody', {}),
                "responses": operation.get('responses', {}),
                "security": operation.get('security', [])
            }

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