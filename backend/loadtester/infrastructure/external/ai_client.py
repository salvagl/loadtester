"""
AI Client Implementation
Multi-provider AI client supporting Google Gemini, Anthropic Claude, and OpenAI
"""

import logging
from typing import Dict, List, Optional

import httpx
from anthropic import AsyncAnthropic
from openai import AsyncOpenAI

from loadtester.domain.interfaces.service_interfaces import AIClientInterface
from loadtester.shared.exceptions.infrastructure_exceptions import ExternalServiceError

logger = logging.getLogger(__name__)


class MultiProviderAIClient(AIClientInterface):
    """Multi-provider AI client with fallback support."""
    
    def __init__(
        self,
        google_api_key: Optional[str] = None,
        anthropic_api_key: Optional[str] = None,
        openai_api_key: Optional[str] = None,
    ):
        self.google_api_key = google_api_key
        self.anthropic_api_key = anthropic_api_key
        self.openai_api_key = openai_api_key
        
        # Initialize clients
        self.anthropic_client = None
        self.openai_client = None
        
        if self.anthropic_api_key:
            self.anthropic_client = AsyncAnthropic(api_key=self.anthropic_api_key)
        
        if self.openai_api_key:
            self.openai_client = AsyncOpenAI(api_key=self.openai_api_key)
        
        # Determine primary provider
        self.primary_provider = self._determine_primary_provider()
        logger.info(f"AI Client initialized with primary provider: {self.primary_provider}")
    
    def _determine_primary_provider(self) -> str:
        """Determine which provider to use as primary."""
        logger.info(f"AI Client keys - Google: {self.google_api_key}, Anthropic: {self.anthropic_api_key}, OpenAI: {self.openai_api_key}")
        if self.google_api_key:
            return "google"
        elif self.anthropic_api_key:
            return "anthropic"
        elif self.openai_api_key:
            return "openai"
        else:
            raise ValueError("At least one AI service API key must be provided")
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None
    ) -> str:
        """Get chat completion from AI service with fallback."""
        providers = [self.primary_provider]
        
        # Add fallback providers
        all_providers = ["google", "anthropic", "openai"]
        for provider in all_providers:
            if provider != self.primary_provider and self._is_provider_available(provider):
                providers.append(provider)
        
        last_error = None
        
        for provider in providers:
            try:
                logger.debug(f"Attempting chat completion with provider: {provider}")
                
                if provider == "google":
                    return await self._google_chat_completion(messages, model, max_tokens, temperature)
                elif provider == "anthropic":
                    return await self._anthropic_chat_completion(messages, model, max_tokens, temperature)
                elif provider == "openai":
                    return await self._openai_chat_completion(messages, model, max_tokens, temperature)
                
            except Exception as e:
                logger.warning(f"Provider {provider} failed: {str(e)}")
                last_error = e
                continue
        
        # All providers failed
        raise ExternalServiceError(f"All AI providers failed. Last error: {str(last_error)}")
    
    async def _google_chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None
    ) -> str:
        """Google Gemini chat completion."""
        if not self.google_api_key:
            raise ExternalServiceError("Google API key not available")
        
        # Use Google Generative AI REST API
        model_name = model or "gemini-2.0-flash"
        url = f"https://generativelanguage.googleapis.com/v1/models/{model_name}:generateContent"
        
        # Convert messages to Google format
        contents = []
        for message in messages:
            role = "user" if message["role"] == "user" else "model"
            contents.append({
                "role": role,
                "parts": [{"text": message["content"]}]
            })
        
        payload = {
            "contents": contents,
            "generationConfig": {
                "maxOutputTokens": max_tokens or 4096,
                "temperature": temperature or 0.7,
            }
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                params={"key": self.google_api_key},
                json=payload,
                timeout=60.0
            )
            
            if response.status_code != 200:
                raise ExternalServiceError(f"Google API error: {response.status_code} - {response.text}")
            
            result = response.json()
            
            if "candidates" not in result or not result["candidates"]:
                raise ExternalServiceError("No response from Google Gemini")
            
            content = result["candidates"][0]["content"]["parts"][0]["text"]
            return content.strip()
    
    async def _anthropic_chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None
    ) -> str:
        """Anthropic Claude chat completion."""
        if not self.anthropic_client:
            raise ExternalServiceError("Anthropic client not available")
        
        # Convert messages to Anthropic format
        anthropic_messages = []
        for message in messages:
            anthropic_messages.append({
                "role": message["role"],
                "content": message["content"]
            })
        
        response = await self.anthropic_client.messages.create(
            model=model or "claude-3-haiku-20240307",
            max_tokens=max_tokens or 4096,
            temperature=temperature or 0.7,
            messages=anthropic_messages
        )
        
        return response.content[0].text.strip()
    
    async def _openai_chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None
    ) -> str:
        """OpenAI chat completion."""
        if not self.openai_client:
            raise ExternalServiceError("OpenAI client not available")
        
        response = await self.openai_client.chat.completions.create(
            model=model or "gpt-3.5-turbo",
            messages=messages,
            max_tokens=max_tokens or 4096,
            temperature=temperature or 0.7
        )
        
        return response.choices[0].message.content.strip()
    
    def _is_provider_available(self, provider: str) -> bool:
        """Check if provider is available."""
        if provider == "google":
            return bool(self.google_api_key)
        elif provider == "anthropic":
            return bool(self.anthropic_client)
        elif provider == "openai":
            return bool(self.openai_client)
        return False
    
    async def is_available(self) -> bool:
        """Check if at least one AI service is available."""
        return any([
            self._is_provider_available("google"),
            self._is_provider_available("anthropic"),
            self._is_provider_available("openai"),
        ])
    
    def get_service_name(self) -> str:
        """Get primary AI service name."""
        return f"Multi-provider AI ({self.primary_provider} primary)"


class OpenAPIParserService:
    """OpenAPI parsing service using AI."""
    
    def __init__(self, ai_client: AIClientInterface):
        self.ai_client = ai_client
    
    async def parse_openapi_spec(self, spec_content: str) -> Dict:
        """Parse OpenAPI specification using AI."""
        prompt = f"""You are a JSON parser. Parse this OpenAPI specification and return ONLY a JSON object.

IMPORTANT: Return ONLY the JSON object, no explanations, no markdown, no text before or after.

Expected JSON structure:
{{
    "info": {{"title": "string", "description": "string", "version": "string"}},
    "servers": [{{ "url": "string" }}],
    "paths": {{}},
    "components": {{}}
}}

OpenAPI Specification to parse:
{spec_content[:8000]}

Return only JSON:"""
        
        messages = [{"role": "user", "content": prompt}]
        response = await self.ai_client.chat_completion(messages)
        
        import json
        import re

        try:
            # Try to parse response directly first
            try:
                return json.loads(response)
            except json.JSONDecodeError:
                # If direct parsing fails, try to extract JSON from the response
                # Look for JSON blocks in the response
                json_patterns = [
                    r'```json\s*(.*?)\s*```',  # JSON in code blocks
                    r'```\s*(.*?)\s*```',      # Any code blocks
                    r'\{.*\}',                 # Any object that looks like JSON
                ]

                for pattern in json_patterns:
                    matches = re.findall(pattern, response, re.DOTALL)
                    for match in matches:
                        try:
                            return json.loads(match.strip())
                        except json.JSONDecodeError:
                            continue

                # If all else fails, log the response for debugging
                logger.error(f"AI response that failed to parse: {response[:500]}...")
                raise ExternalServiceError(f"AI returned invalid JSON for OpenAPI parsing. Response: {response[:200]}...")
        except Exception as e:
            if isinstance(e, ExternalServiceError):
                raise
            raise ExternalServiceError(f"Error parsing AI response: {str(e)}")
    
    async def extract_endpoints(self, parsed_spec: Dict) -> List[Dict]:
        """Extract endpoints from parsed OpenAPI spec."""
        import json

        prompt = f"""You are a JSON extractor. Extract endpoints from this OpenAPI specification and return ONLY a JSON array.

IMPORTANT: Return ONLY the JSON array, no explanations, no markdown, no text before or after.
IMPORTANT: Do not use null values. Use empty string "" for missing text fields and empty object {{}} for missing objects.

Expected array structure:
[
    {{
        "path": "/users/{{id}}",
        "method": "GET",
        "summary": "Get user by ID",
        "description": "Retrieves a user by their ID",
        "parameters": [],
        "requestBody": {{}},
        "responses": {{}}
    }}
]

OpenAPI Specification:
{json.dumps(parsed_spec, indent=2)[:6000]}

Return only JSON array:"""
        
        messages = [{"role": "user", "content": prompt}]
        response = await self.ai_client.chat_completion(messages)
        
        import json
        import re

        try:
            # Try to parse response directly first
            try:
                parsed_data = json.loads(response)
                # Log the parsed data for debugging
                logger.debug(f"Parsed endpoints data: {json.dumps(parsed_data, indent=2)[:1000]}...")
                return parsed_data
            except json.JSONDecodeError:
                # If direct parsing fails, try to extract JSON from the response
                json_patterns = [
                    r'```json\s*(.*?)\s*```',  # JSON in code blocks
                    r'```\s*(.*?)\s*```',      # Any code blocks
                    r'\[.*\]',                 # Any array that looks like JSON
                ]

                for pattern in json_patterns:
                    matches = re.findall(pattern, response, re.DOTALL)
                    for match in matches:
                        try:
                            parsed_data = json.loads(match.strip())
                            # Log the parsed data for debugging
                            logger.debug(f"Parsed endpoints data from pattern: {json.dumps(parsed_data, indent=2)[:1000]}...")
                            return parsed_data
                        except json.JSONDecodeError:
                            continue

                # If all else fails, log the response for debugging
                logger.error(f"AI response that failed to parse for endpoints: {response[:500]}...")
                raise ExternalServiceError(f"AI returned invalid JSON for endpoint extraction. Response: {response[:200]}...")
        except Exception as e:
            if isinstance(e, ExternalServiceError):
                raise
            raise ExternalServiceError(f"Error parsing AI response for endpoints: {str(e)}")
    
    async def validate_spec(self, spec_content: str) -> bool:
        """Validate OpenAPI specification format."""
        prompt = f"""
        Validate if this is a valid OpenAPI specification (version 3.0+).
        Return only "true" or "false".
        
        Spec (first 2000 chars):
        {spec_content[:2000]}
        """
        
        messages = [{"role": "user", "content": prompt}]
        response = await self.ai_client.chat_completion(messages)
        
        return response.strip().lower() == "true"
    
    async def get_endpoint_schema(
        self,
        parsed_spec: Dict,
        path: str,
        method: str
    ) -> Optional[Dict]:
        """Get schema for specific endpoint."""
        import json

        prompt = f"""
        Extract the complete schema for the endpoint {method.upper()} {path} from this OpenAPI spec.
        Return JSON with:
        {{
            "parameters": [],
            "requestBody": {{}},
            "responses": {{}},
            "security": []
        }}

        OpenAPI Spec:
        {json.dumps(parsed_spec, indent=2)[:6000]}

        Only return JSON, no explanations.
        """
        
        messages = [{"role": "user", "content": prompt}]
        response = await self.ai_client.chat_completion(messages)
        
        try:
            import json
            return json.loads(response)
        except json.JSONDecodeError:
            return None