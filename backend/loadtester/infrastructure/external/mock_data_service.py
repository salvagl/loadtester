"""
Mock Data Generator Service Implementation
AI-powered mock data generation for load testing
"""

import json
import logging
from typing import Dict, List
from uuid import uuid4

from faker import Faker

from loadtester.domain.entities.domain_entities import Endpoint
from loadtester.domain.interfaces.service_interfaces import (
    AIClientInterface, MockDataGeneratorServiceInterface
)
from loadtester.shared.exceptions.infrastructure_exceptions import ExternalServiceError

logger = logging.getLogger(__name__)


class MockDataGeneratorService(MockDataGeneratorServiceInterface):
    """Mock data generation service using AI and Faker."""
    
    def __init__(self, ai_client: AIClientInterface):
        self.ai_client = ai_client
        self.faker = Faker()
    
    async def generate_mock_data(
        self, 
        endpoint: Endpoint, 
        schema: Dict, 
        count: int = 100
    ) -> List[Dict]:
        """Generate mock data for endpoint based on schema."""
        logger.info(f"Generating {count} mock data records for {endpoint.endpoint_name}")
        
        try:
            # First, analyze the endpoint to understand data requirements
            data_template = await self._analyze_endpoint_requirements(endpoint, schema)
            
            # Generate mock data using AI
            if await self.ai_client.is_available():
                mock_data = await self._generate_with_ai(endpoint, data_template, count)
            else:
                mock_data = await self._generate_with_faker(endpoint, data_template, count)
            
            # Validate generated data
            valid_data = []
            for item in mock_data:
                if await self.validate_generated_data(item, schema):
                    valid_data.append(item)
            
            logger.info(f"Generated {len(valid_data)} valid mock data records")
            return valid_data
            
        except Exception as e:
            logger.error(f"Error generating mock data: {str(e)}")
            # Fallback to basic Faker data
            return await self._generate_basic_fallback_data(endpoint, count)
    
    async def _analyze_endpoint_requirements(self, endpoint: Endpoint, schema: Dict) -> Dict:
        """Analyze endpoint to understand data requirements."""
        data_template = {
            "path_params": {},
            "query_params": {},
            "body": None,
            "headers": {}
        }
        
        # Extract path parameters
        path = endpoint.endpoint_path
        if "{" in path:
            import re
            path_params = re.findall(r'\{([^}]+)\}', path)
            for param in path_params:
                data_template["path_params"][param] = self._get_param_type(param)
        
        # Extract from schema if available
        if schema:
            if "parameters" in schema:
                for param in schema["parameters"]:
                    param_name = param.get("name", "")
                    param_in = param.get("in", "")
                    param_type = param.get("schema", {}).get("type", "string")
                    
                    if param_in == "path":
                        data_template["path_params"][param_name] = param_type
                    elif param_in == "query":
                        data_template["query_params"][param_name] = param_type
            
            if "requestBody" in schema and endpoint.http_method.upper() in ["POST", "PUT", "PATCH"]:
                content = schema["requestBody"].get("content", {})
                if "application/json" in content:
                    data_template["body"] = content["application/json"].get("schema", {})
        
        return data_template
    
    def _get_param_type(self, param_name: str) -> str:
        """Infer parameter type from name."""
        param_lower = param_name.lower()
        
        if "id" in param_lower:
            return "integer"
        elif "email" in param_lower:
            return "email"
        elif "name" in param_lower:
            return "string"
        elif "date" in param_lower:
            return "date"
        elif "time" in param_lower:
            return "datetime"
        elif "phone" in param_lower:
            return "phone"
        elif "url" in param_lower or "uri" in param_lower:
            return "url"
        else:
            return "string"
    
    async def _generate_with_ai(
        self, 
        endpoint: Endpoint, 
        data_template: Dict, 
        count: int
    ) -> List[Dict]:
        """Generate mock data using AI."""
        prompt = f"""
        Generate {count} realistic mock data records for API endpoint testing.
        
        Endpoint: {endpoint.http_method} {endpoint.endpoint_path}
        Description: {endpoint.description or 'No description available'}
        
        Data template structure:
        {json.dumps(data_template, indent=2)}
        
        Requirements:
        1. Generate realistic, varied data
        2. Ensure data types match the schema
        3. Use realistic values (real names, emails, etc.)
        4. Return as JSON array
        5. Include all required fields
        
        Return only the JSON array, no explanations.
        """
        
        messages = [{"role": "user", "content": prompt}]
        response = await self.ai_client.chat_completion(messages, max_tokens=4000)
        
        try:
            mock_data = json.loads(response.strip())
            if not isinstance(mock_data, list):
                raise ValueError("Response is not a list")
            return mock_data
            
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"AI returned invalid JSON: {str(e)}")
            return await self._generate_with_faker(endpoint, data_template, count)
    
    async def _generate_with_faker(
        self, 
        endpoint: Endpoint, 
        data_template: Dict, 
        count: int
    ) -> List[Dict]:
        """Generate mock data using Faker library."""
        logger.info("Generating mock data with Faker")
        
        mock_data = []
        
        for _ in range(count):
            record = {}
            
            # Generate path parameters
            if data_template.get("path_params"):
                record["path_params"] = {}
                for param, param_type in data_template["path_params"].items():
                    record["path_params"][param] = self._generate_faker_value(param_type, param)
            
            # Generate query parameters
            if data_template.get("query_params"):
                record["query_params"] = {}
                for param, param_type in data_template["query_params"].items():
                    record["query_params"][param] = self._generate_faker_value(param_type, param)
            
            # Generate body
            if data_template.get("body") and endpoint.http_method.upper() in ["POST", "PUT", "PATCH"]:
                record["body"] = self._generate_body_from_schema(data_template["body"])
            
            mock_data.append(record)
        
        return mock_data
    
    def _generate_faker_value(self, data_type: str, param_name: str = ""):
        """Generate value using Faker based on type and parameter name."""
        param_lower = param_name.lower()
        
        if data_type == "integer" or "id" in param_lower:
            return self.faker.random_int(min=1, max=10000)
        elif data_type == "email" or "email" in param_lower:
            return self.faker.email()
        elif data_type == "phone" or "phone" in param_lower:
            return self.faker.phone_number()
        elif data_type == "url" or "url" in param_lower:
            return self.faker.url()
        elif data_type == "date" or "date" in param_lower:
            return self.faker.date_between(start_date='-1y', end_date='today').isoformat()
        elif data_type == "datetime" or "time" in param_lower:
            return self.faker.date_time_between(start_date='-1y', end_date='now').isoformat()
        elif "name" in param_lower:
            return self.faker.name()
        elif "address" in param_lower:
            return self.faker.address()
        elif "company" in param_lower:
            return self.faker.company()
        elif "country" in param_lower:
            return self.faker.country()
        elif "city" in param_lower:
            return self.faker.city()
        elif "description" in param_lower:
            return self.faker.text(max_nb_chars=200)
        elif "uuid" in param_lower:
            return str(uuid4())
        else:
            return self.faker.word()
    
    def _generate_body_from_schema(self, schema: Dict) -> Dict:
        """Generate request body from JSON schema."""
        if not schema:
            return {}
        
        schema_type = schema.get("type", "object")
        
        if schema_type == "object":
            body = {}
            properties = schema.get("properties", {})
            
            for prop_name, prop_schema in properties.items():
                body[prop_name] = self._generate_value_from_property_schema(prop_name, prop_schema)
            
            return body
        
        elif schema_type == "array":
            items_schema = schema.get("items", {})
            return [self._generate_value_from_property_schema("item", items_schema)]
        
        else:
            return self._generate_value_from_property_schema("value", schema)
    
    def _generate_value_from_property_schema(self, prop_name: str, prop_schema: Dict):
        """Generate value for a specific property schema."""
        prop_type = prop_schema.get("type", "string")
        prop_format = prop_schema.get("format", "")
        
        if prop_type == "string":
            if prop_format == "email":
                return self.faker.email()
            elif prop_format == "date":
                return self.faker.date().isoformat()
            elif prop_format == "date-time":
                return self.faker.date_time().isoformat()
            elif prop_format == "uuid":
                return str(uuid4())
            else:
                return self._generate_faker_value("string", prop_name)
        
        elif prop_type == "integer":
            minimum = prop_schema.get("minimum", 1)
            maximum = prop_schema.get("maximum", 1000)
            return self.faker.random_int(min=minimum, max=maximum)
        
        elif prop_type == "number":
            return round(self.faker.random.uniform(0, 1000), 2)
        
        elif prop_type == "boolean":
            return self.faker.boolean()
        
        elif prop_type == "array":
            items = prop_schema.get("items", {})
            return [self._generate_value_from_property_schema("item", items)]
        
        elif prop_type == "object":
            return self._generate_body_from_schema(prop_schema)
        
        else:
            return self._generate_faker_value("string", prop_name)
    
    async def _generate_basic_fallback_data(self, endpoint: Endpoint, count: int) -> List[Dict]:
        """Generate basic fallback data when other methods fail."""
        logger.info("Using basic fallback data generation")
        
        mock_data = []
        
        for i in range(count):
            record = {
                "path_params": {"id": i + 1},
                "query_params": {"page": 1, "limit": 10},
            }
            
            if endpoint.http_method.upper() in ["POST", "PUT", "PATCH"]:
                record["body"] = {
                    "name": self.faker.name(),
                    "email": self.faker.email(),
                    "description": self.faker.text(max_nb_chars=100),
                    "value": self.faker.random_int(min=1, max=1000),
                    "active": self.faker.boolean(),
                }
            
            mock_data.append(record)
        
        return mock_data
    
    async def generate_path_parameters(self, path: str, schema: Dict) -> Dict:
        """Generate mock path parameters."""
        import re
        path_params = {}
        
        # Extract parameter names from path
        param_names = re.findall(r'\{([^}]+)\}', path)
        
        for param_name in param_names:
            param_type = self._get_param_type(param_name)
            path_params[param_name] = self._generate_faker_value(param_type, param_name)
        
        return path_params
    
    async def generate_query_parameters(self, schema: Dict) -> Dict:
        """Generate mock query parameters."""
        query_params = {}
        
        if schema and "parameters" in schema:
            for param in schema["parameters"]:
                if param.get("in") == "query":
                    param_name = param.get("name", "")
                    param_type = param.get("schema", {}).get("type", "string")
                    query_params[param_name] = self._generate_faker_value(param_type, param_name)
        
        # Add common query parameters
        query_params.update({
            "page": self.faker.random_int(min=1, max=10),
            "limit": self.faker.random_int(min=10, max=100),
        })
        
        return query_params
    
    async def generate_request_body(self, schema: Dict) -> Dict:
        """Generate mock request body."""
        if not schema:
            return {}
        
        return self._generate_body_from_schema(schema)
    
    async def validate_generated_data(self, data: Dict, schema: Dict) -> bool:
        """Validate generated data against schema."""
        try:
            # Basic validation - check if required fields are present
            if not data:
                return False
            
            # For now, just check if data is a valid dictionary
            return isinstance(data, dict) and bool(data)
            
        except Exception as e:
            logger.warning(f"Data validation failed: {str(e)}")
            return False