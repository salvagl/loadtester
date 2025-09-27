"""
K6 Runner Service Implementation
Handles K6 script generation, execution, and result parsing
"""

import asyncio
import json
import logging
import os
import tempfile
from pathlib import Path
from typing import Dict, List, Optional

from app.domain.entities.test_scenario import Endpoint
from app.domain.interfaces.ai_services import (
    K6RunnerServiceInterface, K6ScriptGeneratorServiceInterface
)
from app.shared.exceptions.infrastructure import ExternalServiceError

logger = logging.getLogger(__name__)


class K6ScriptGeneratorService(K6ScriptGeneratorServiceInterface):
    """K6 script generation service."""
    
    def __init__(self, ai_client):
        self.ai_client = ai_client
    
    async def generate_k6_script(
        self, 
        endpoint: Endpoint, 
        test_data: List[Dict], 
        scenario_config: Dict
    ) -> str:
        """Generate K6 script for load testing."""
        logger.info(f"Generating K6 script for {endpoint.http_method} {endpoint.endpoint_path}")
        
        # Create K6 script template
        script_template = self._create_k6_script_template(endpoint, test_data, scenario_config)
        
        # Use AI to enhance and validate the script
        enhanced_script = await self._enhance_script_with_ai(script_template, endpoint, scenario_config)
        
        return enhanced_script
    
    def _create_k6_script_template(
        self, 
        endpoint: Endpoint, 
        test_data: List[Dict], 
        scenario_config: Dict
    ) -> str:
        """Create basic K6 script template."""
        concurrent_users = scenario_config.get("concurrent_users", 1)
        duration = scenario_config.get("duration", 60)
        ramp_up = scenario_config.get("ramp_up", 10)
        ramp_down = scenario_config.get("ramp_down", 10)
        
        # Build auth headers
        auth_headers = self._build_auth_headers(endpoint)
        
        # Build request body
        request_body = self._build_request_body(endpoint, test_data)
        
        # Build URL with parameters
        url_template = self._build_url_template(endpoint, test_data)
        
        script = f"""
import http from 'k6/http';
import {{ check, sleep }} from 'k6';
import {{ Rate }} from 'k6/metrics';

// Custom metrics
const errorRate = new Rate('errors');

// Test data
const testData = {json.dumps(test_data, indent=2)};

// Configuration
export const options = {{
    stages: [
        {{ duration: '{ramp_up}s', target: {concurrent_users} }},
        {{ duration: '{duration}s', target: {concurrent_users} }},
        {{ duration: '{ramp_down}s', target: 0 }},
    ],
    thresholds: {{
        http_req_duration: ['p(95)<500'], // 95% of requests under 500ms
        http_req_failed: ['rate<0.1'],   // Error rate under 10%
        errors: ['rate<0.1'],            // Custom error rate under 10%
    }},
}};

export default function() {{
    // Select random test data
    const data = testData[Math.floor(Math.random() * testData.length)];
    
    // Build URL
    let url = '{endpoint.endpoint_path}';
    {url_template}
    
    // Prepare headers
    const headers = {{
        'Content-Type': 'application/json',
        {auth_headers}
    }};
    
    // Prepare request parameters
    const params = {{
        headers: headers,
        timeout: '{endpoint.timeout_ms}ms',
    }};
    
    // Make request
    let response;
    {request_body}
    
    // Check response
    const result = check(response, {{
        'status is 2xx': (r) => r.status >= 200 && r.status < 300,
        'response time < 1000ms': (r) => r.timings.duration < 1000,
    }});
    
    // Record errors
    errorRate.add(!result);
    
    // Think time
    sleep(1);
}}
"""
        return script.strip()
    
    def _build_auth_headers(self, endpoint: Endpoint) -> str:
        """Build authentication headers for K6 script."""
        if not endpoint.auth_config:
            return "'User-Agent': 'LoadTester-K6/1.0',"
        
        auth_type = endpoint.auth_config.auth_type.value
        
        if auth_type == "bearer_token":
            token = endpoint.auth_config.token
            return f"'Authorization': 'Bearer {token}',\n        'User-Agent': 'LoadTester-K6/1.0',"
        
        elif auth_type == "api_key":
            api_key = endpoint.auth_config.api_key
            header_name = endpoint.auth_config.header_name or "X-API-Key"
            return f"'{header_name}': '{api_key}',\n        'User-Agent': 'LoadTester-K6/1.0',"
        
        return "'User-Agent': 'LoadTester-K6/1.0',"
    
    def _build_request_body(self, endpoint: Endpoint, test_data: List[Dict]) -> str:
        """Build request body for K6 script."""
        method = endpoint.http_method.upper()
        
        if method in ["GET", "DELETE", "HEAD"]:
            return f"response = http.{method.lower()}(url, params);"
        
        elif method in ["POST", "PUT", "PATCH"]:
            return f"""
    // Prepare body
    const body = data.body ? JSON.stringify(data.body) : null;
    
    response = http.{method.lower()}(url, body, params);"""
        
        else:
            return f"response = http.request('{method}', url, null, params);"
    
    def _build_url_template(self, endpoint: Endpoint, test_data: List[Dict]) -> str:
        """Build URL template with parameter substitution."""
        path = endpoint.endpoint_path
        
        # Handle path parameters
        url_building = []
        
        if "{" in path:
            url_building.append("""
    // Replace path parameters
    if (data.path_params) {
        for (const [key, value] of Object.entries(data.path_params)) {
            url = url.replace(`{${key}}`, value);
        }
    }""")
        
        # Handle query parameters
        url_building.append("""
    // Add query parameters
    if (data.query_params) {
        const queryString = Object.entries(data.query_params)
            .map(([key, value]) => `${key}=${encodeURIComponent(value)}`)
            .join('&');
        url += '?' + queryString;
    }""")
        
        # Add base URL
        base_url = getattr(endpoint, 'api', {}).get('base_url', 'http://localhost')
        if hasattr(endpoint, 'api') and endpoint.api and endpoint.api.base_url:
            base_url = endpoint.api.base_url
        
        url_building.insert(0, f"url = '{base_url}' + url;")
        
        return "\n    ".join(url_building)
    
    async def _enhance_script_with_ai(
        self, 
        script_template: str, 
        endpoint: Endpoint, 
        scenario_config: Dict
    ) -> str:
        """Enhance K6 script using AI."""
        prompt = f"""
        Review and enhance this K6 load testing script. Make sure it:
        1. Has proper error handling
        2. Includes meaningful checks
        3. Has appropriate think time
        4. Is syntactically correct
        5. Follows K6 best practices
        
        Endpoint: {endpoint.http_method} {endpoint.endpoint_path}
        Expected volumetry: {endpoint.expected_volumetry} req/min
        Expected users: {endpoint.expected_concurrent_users}
        
        Current script:
        {script_template}
        
        Return only the enhanced K6 script, no explanations.
        """
        
        messages = [{"role": "user", "content": prompt}]
        enhanced_script = await self.ai_client.chat_completion(messages, max_tokens=3000)
        
        # Clean up the response (remove markdown if present)
        enhanced_script = enhanced_script.strip()
        if enhanced_script.startswith("```"):
            lines = enhanced_script.split("\n")
            enhanced_script = "\n".join(lines[1:-1])
        
        return enhanced_script
    
    async def generate_scenario_options(
        self, 
        concurrent_users: int, 
        duration: int, 
        ramp_up: int, 
        ramp_down: int
    ) -> Dict:
        """Generate K6 scenario options."""
        return {
            "stages": [
                {"duration": f"{ramp_up}s", "target": concurrent_users},
                {"duration": f"{duration}s", "target": concurrent_users},
                {"duration": f"{ramp_down}s", "target": 0},
            ],
            "thresholds": {
                "http_req_duration": ["p(95)<500"],
                "http_req_failed": ["rate<0.1"],
            },
        }
    
    async def validate_script(self, script: str) -> bool:
        """Validate generated K6 script syntax."""
        # Basic syntax validation
        required_patterns = [
            "import http from 'k6/http'",
            "export default function",
            "export const options",
        ]
        
        for pattern in required_patterns:
            if pattern not in script:
                logger.warning(f"K6 script missing required pattern: {pattern}")
                return False
        
        return True


class K6RunnerService(K6RunnerServiceInterface):
    """K6 execution service."""
    
    def __init__(self, scripts_path: str, results_path: str):
        self.scripts_path = Path(scripts_path)
        self.results_path = Path(results_path)
        
        # Ensure directories exist
        self.scripts_path.mkdir(parents=True, exist_ok=True)
        self.results_path.mkdir(parents=True, exist_ok=True)
    
    async def execute_k6_script(
        self, 
        script_content: str, 
        execution_id: int,
        options: Optional[Dict] = None
    ) -> Dict:
        """Execute K6 script and return results."""
        logger.info(f"Executing K6 script for execution {execution_id}")
        
        # Save script to file
        script_file = self.scripts_path / f"script_{execution_id}.js"
        with open(script_file, 'w') as f:
            f.write(script_content)
        
        # Prepare output file
        output_file = self.results_path / f"results_{execution_id}.json"
        
        # Build K6 command
        cmd = [
            "docker", "exec", "loadtester-k6",
            "k6", "run",
            "--out", f"json={output_file}",
            "--summary-export", f"{output_file}.summary",
            f"/scripts/generated/script_{execution_id}.js"
        ]
        
        try:
            # Execute K6
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                error_msg = stderr.decode() if stderr else "Unknown K6 error"
                logger.error(f"K6 execution failed: {error_msg}")
                raise ExternalServiceError(f"K6 execution failed: {error_msg}")
            
            # Parse results
            results = await self.parse_k6_results(str(output_file))
            
            # Add execution info
            results["execution_info"] = {
                "execution_id": execution_id,
                "script_file": str(script_file),
                "output_file": str(output_file),
                "stdout": stdout.decode(),
                "stderr": stderr.decode(),
            }
            
            logger.info(f"K6 execution completed for execution {execution_id}")
            return results
            
        except Exception as e:
            logger.error(f"Error executing K6 script: {str(e)}")
            raise ExternalServiceError(f"K6 execution error: {str(e)}")
    
    async def parse_k6_results(self, results_path: str) -> Dict:
        """Parse K6 execution results."""
        try:
            # Read summary file if available
            summary_file = f"{results_path}.summary"
            if os.path.exists(summary_file):
                with open(summary_file, 'r') as f:
                    summary_data = json.load(f)
                return self._process_k6_summary(summary_data)
            
            # Fallback to parsing JSON output
            if os.path.exists(results_path):
                with open(results_path, 'r') as f:
                    lines = f.readlines()
                
                metrics = {}
                for line in lines:
                    try:
                        data = json.loads(line)
                        if data.get("type") == "Point":
                            metric_name = data.get("metric")
                            if metric_name:
                                if metric_name not in metrics:
                                    metrics[metric_name] = []
                                metrics[metric_name].append(data.get("data", {}))
                    except json.JSONDecodeError:
                        continue
                
                return self._process_k6_metrics(metrics)
            
            return {"error": "No results file found"}
            
        except Exception as e:
            logger.error(f"Error parsing K6 results: {str(e)}")
            return {"error": f"Failed to parse results: {str(e)}"}
    
    def _process_k6_summary(self, summary_data: Dict) -> Dict:
        """Process K6 summary data."""
        metrics = summary_data.get("metrics", {})
        
        return {
            "metrics": {
                "http_req_duration": {
                    "avg": metrics.get("http_req_duration", {}).get("avg"),
                    "min": metrics.get("http_req_duration", {}).get("min"),
                    "max": metrics.get("http_req_duration", {}).get("max"),
                    "p(95)": metrics.get("http_req_duration", {}).get("p(95)"),
                    "p(99)": metrics.get("http_req_duration", {}).get("p(99)"),
                },
                "http_reqs": {
                    "count": metrics.get("http_reqs", {}).get("count"),
                    "rate": metrics.get("http_reqs", {}).get("rate"),
                },
                "http_req_failed": {
                    "count": metrics.get("http_req_failed", {}).get("count"),
                    "rate": metrics.get("http_req_failed", {}).get("rate"),
                },
                "data_sent": metrics.get("data_sent", {}),
                "data_received": metrics.get("data_received", {}),
            },
            "summary": summary_data
        }
    
    def _process_k6_metrics(self, metrics: Dict) -> Dict:
        """Process K6 metrics from JSON output."""
        processed = {"metrics": {}}
        
        for metric_name, data_points in metrics.items():
            if data_points:
                # Calculate basic statistics
                values = [dp.get("value", 0) for dp in data_points if "value" in dp]
                if values:
                    processed["metrics"][metric_name] = {
                        "avg": sum(values) / len(values),
                        "min": min(values),
                        "max": max(values),
                        "count": len(values),
                    }
        
        return processed
    
    async def is_k6_available(self) -> bool:
        """Check if K6 is available for execution."""
        try:
            process = await asyncio.create_subprocess_exec(
                "docker", "exec", "loadtester-k6", "k6", "version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            await process.communicate()
            return process.returncode == 0
            
        except Exception:
            return False
    
    async def get_k6_version(self) -> str:
        """Get K6 version."""
        try:
            process = await asyncio.create_subprocess_exec(
                "docker", "exec", "loadtester-k6", "k6", "version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, _ = await process.communicate()
            
            if process.returncode == 0:
                return stdout.decode().strip()
            
            return "Unknown"
            
        except Exception:
            return "Error getting version"