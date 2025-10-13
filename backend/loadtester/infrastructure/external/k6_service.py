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

from loadtester.domain.entities.domain_entities import Endpoint
from loadtester.domain.interfaces.service_interfaces import (
    K6RunnerServiceInterface, K6ScriptGeneratorServiceInterface
)
from loadtester.shared.exceptions.infrastructure_exceptions import ExternalServiceError

logger = logging.getLogger(__name__)


class K6ScriptGeneratorService(K6ScriptGeneratorServiceInterface):
    """K6 script generation service."""
    
    def __init__(self, ai_client):
        self.ai_client = ai_client

    def _ensure_integer(self, value) -> int:
        """Ensure value is an integer, converting from float if necessary.

        This is crucial for K6 compatibility as K6 expects integer values
        for duration, target users, etc. and will fail if it receives decimals.

        Args:
            value: The value to convert (int, float, or string)

        Returns:
            int: The value converted to integer
        """
        try:
            # Convert to float first to handle string numbers, then to int
            return int(float(value))
        except (ValueError, TypeError):
            # If conversion fails, return 1 as safe default
            logger.warning(f"Failed to convert {value} to integer, using default value 1")
            return 1

    def _ensure_integer_values_in_script(self, script: str) -> str:
        """Post-process script to ensure all numeric values are integers.

        This is a safety net to catch any decimal values that might have been
        introduced by AI enhancement and convert them to integers.
        """
        import re

        # Pattern to find decimal numbers like 1.6666666666666667, 100/60, etc.
        # This will find patterns like: number/number or decimal numbers
        decimal_patterns = [
            # Match division operations that could result in decimals
            (r'(\d+)\s*/\s*(\d+)', lambda m: str(int(float(m.group(1)) / float(m.group(2))))),
            # Match decimal numbers (but preserve strings like '30s')
            (r'\b(\d+\.\d+)(?![a-zA-Z])', lambda m: str(int(float(m.group(1))))),
        ]

        for pattern, replacement in decimal_patterns:
            script = re.sub(pattern, replacement, script)

        return script
    
    async def generate_k6_script(
        self,
        endpoint: Endpoint,
        test_data: List[Dict],
        scenario_config: Dict
    ) -> str:
        """Generate K6 script for load testing."""
        logger.info(f"Generating K6 script for {endpoint.http_method} {endpoint.endpoint_path}")

        # Debug: Check if endpoint has API attached
        if hasattr(endpoint, 'api') and endpoint.api:
            logger.info(f"[DEBUG] Endpoint has API object with base_url: {endpoint.api.base_url if hasattr(endpoint.api, 'base_url') else 'NO BASE_URL ATTR'}")
        else:
            logger.warning(f"[DEBUG] Endpoint does NOT have API object attached!")

        # Create K6 script template
        script_template = self._create_k6_script_template(endpoint, test_data, scenario_config)

        # Log a snippet of the template to see the URL
        template_lines = script_template.split('\n')
        for i, line in enumerate(template_lines):
            if 'url =' in line.lower() or 'let url' in line.lower() or 'const url' in line.lower():
                logger.info(f"[DEBUG] Template URL line {i}: {line.strip()}")

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
        # Ensure all numeric values are integers for K6 compatibility
        concurrent_users = self._ensure_integer(scenario_config.get("concurrent_users", 1))
        target_volumetry = self._ensure_integer(scenario_config.get("target_volumetry", 60))
        duration = self._ensure_integer(scenario_config.get("duration", 60))
        ramp_up = self._ensure_integer(scenario_config.get("ramp_up", 10))
        ramp_down = self._ensure_integer(scenario_config.get("ramp_down", 10))

        # Calculate think time (sleep) to achieve target volumetry
        # Formula: sleep_time = (concurrent_users * 60) / target_volumetry
        # This ensures the combined load of all users matches the target volumetry
        if target_volumetry > 0 and concurrent_users > 0:
            sleep_time = (concurrent_users * 60.0) / target_volumetry
            # Ensure at least 0.1 seconds between requests
            sleep_time = max(0.1, sleep_time)
        else:
            sleep_time = 1.0

        # Build auth headers
        auth_headers = self._build_auth_headers(endpoint)

        # Build request body
        request_body = self._build_request_body(endpoint, test_data)

        # Build URL with parameters
        url_template = self._build_url_template(endpoint, test_data)

        # Ensure timeout is also an integer
        timeout_ms = self._ensure_integer(getattr(endpoint, 'timeout_ms', 30000))

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
        timeout: '{timeout_ms}ms',
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

    // Think time - calculated to achieve target volumetry
    // sleep_time = (concurrent_users * 60) / target_volumetry
    sleep({sleep_time});
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
        base_url = 'http://host.docker.internal:8000'  # Default fallback
        if hasattr(endpoint, 'api') and endpoint.api and hasattr(endpoint.api, 'base_url') and endpoint.api.base_url:
            base_url = endpoint.api.base_url
            logger.info(f"Using API base URL: {base_url}")
        else:
            logger.warning(f"No API base_url found for endpoint, using default: {base_url}")

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
        Review and enhance this K6 load testing script. IMPORTANT REQUIREMENTS:
        1. Keep the exact same export const options structure with stages, do NOT change to scenarios
        2. ALL numeric values (duration, target, rate, etc.) MUST be integers, never decimals
        3. Use Math.floor() or Math.ceil() if you need to convert any calculations to integers
        4. Has proper error handling
        5. Includes meaningful checks
        6. Has appropriate think time
        7. Is syntactically correct
        8. Follows K6 best practices
        9. CRITICAL: Keep the EXACT same testData array as provided - DO NOT modify, replace, or simplify the test data

        CRITICAL: Do NOT use division operations that result in decimals. If you need to convert req/min to req/sec, use Math.floor() or Math.ceil().
        CRITICAL: The testData array contains mock data generated from OpenAPI schema - preserve it exactly as provided, including all fields and values.

        Endpoint: {endpoint.http_method} {endpoint.endpoint_path}
        Expected volumetry: {endpoint.expected_volumetry} req/min
        Expected users: {endpoint.expected_concurrent_users}

        Current script:
        {script_template}

        Return only the enhanced K6 script with integer values only, no explanations.
        """
        
        messages = [{"role": "user", "content": prompt}]
        enhanced_script = await self.ai_client.chat_completion(messages, max_tokens=3000)
        
        # Clean up the response (remove markdown if present)
        enhanced_script = enhanced_script.strip()
        if enhanced_script.startswith("```"):
            lines = enhanced_script.split("\n")
            enhanced_script = "\n".join(lines[1:-1])

        # Post-process to ensure no decimal values remain
        enhanced_script = self._ensure_integer_values_in_script(enhanced_script)

        return enhanced_script
    
    async def generate_scenario_options(
        self,
        concurrent_users: int,
        duration: int,
        ramp_up: int,
        ramp_down: int
    ) -> Dict:
        """Generate K6 scenario options."""
        # Ensure all values are integers for K6 compatibility
        concurrent_users = self._ensure_integer(concurrent_users)
        duration = self._ensure_integer(duration)
        ramp_up = self._ensure_integer(ramp_up)
        ramp_down = self._ensure_integer(ramp_down)

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
        
        # Build K6 command (local execution with proper user and environment)
        cmd = [
            "sudo", "-u", "appuser",
            "env", "HOME=/home/appuser",
            "k6", "run",
            "--out", f"json={output_file}",
            "--summary-export", f"{output_file}.summary",
            str(script_file)
        ]

        # Execute K6 as appuser with proper environment
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env={
                **os.environ,
                'HOME': '/home/appuser',
                'USER': 'appuser',
                'XDG_CONFIG_HOME': '/home/appuser/.config'
            }
        )

        stdout, stderr = await process.communicate()

        # Parse results FIRST, even if K6 failed (thresholds can fail but still produce results)
        try:
            results = await self.parse_k6_results(str(output_file))
        except Exception as parse_error:
            logger.error(f"Error parsing K6 results: {str(parse_error)}")
            # Return minimal results with error info
            results = {
                "metrics": {},
                "error": f"Failed to parse results: {str(parse_error)}"
            }

        # Add execution info
        results["execution_info"] = {
            "execution_id": execution_id,
            "script_file": str(script_file),
            "output_file": str(output_file),
            "stdout": stdout.decode(),
            "stderr": stderr.decode(),
            "return_code": process.returncode,
        }

        # If K6 failed, log it but don't raise exception (results are still valid)
        if process.returncode != 0:
            error_msg = stderr.decode() if stderr else "Unknown K6 error"
            logger.warning(f"K6 execution completed with non-zero exit code ({process.returncode}): {error_msg}")
            # Add error info to results but don't fail
            results["execution_info"]["k6_error"] = error_msg
            results["execution_info"]["k6_failed"] = True
        else:
            results["execution_info"]["k6_failed"] = False

        logger.info(f"K6 execution completed for execution {execution_id}")
        return results
    
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

        # Extract http_req_duration metrics
        http_req_duration = metrics.get("http_req_duration", {})
        duration_metrics = {
            "avg": http_req_duration.get("avg"),
            "min": http_req_duration.get("min"),
            "med": http_req_duration.get("med"),
            "max": http_req_duration.get("max"),
            "p(90)": http_req_duration.get("p(90)"),
            "p(95)": http_req_duration.get("p(95)"),
            "p(99)": http_req_duration.get("p(99)"),  # May be None if not in summary
        }

        # Extract http_reqs metrics
        http_reqs = metrics.get("http_reqs", {})
        reqs_metrics = {
            "count": http_reqs.get("count", 0),
            "rate": http_reqs.get("rate", 0),
        }

        # Extract http_req_failed metrics
        http_req_failed = metrics.get("http_req_failed", {})
        # Calculate failed count from passes/fails or from rate
        failed_count = http_req_failed.get("passes", 0)
        failed_rate = http_req_failed.get("value", 0)  # This is the actual failure rate (0-1)

        failed_metrics = {
            "count": failed_count,
            "rate": failed_rate,
        }

        # Extract data transfer metrics
        data_sent = metrics.get("data_sent", {})
        data_received = metrics.get("data_received", {})

        # Extract checks metrics
        checks = metrics.get("checks", {})
        checks_metrics = {
            "passes": checks.get("passes", 0),
            "fails": checks.get("fails", 0),
            "value": checks.get("value", 0),  # Success rate
        }

        # Extract iteration metrics
        iterations = metrics.get("iterations", {})
        iteration_duration = metrics.get("iteration_duration", {})

        return {
            "metrics": {
                "http_req_duration": duration_metrics,
                "http_reqs": reqs_metrics,
                "http_req_failed": failed_metrics,
                "data_sent": data_sent,
                "data_received": data_received,
                "checks": checks_metrics,
                "iterations": {
                    "count": iterations.get("count", 0),
                    "rate": iterations.get("rate", 0),
                },
                "iteration_duration": {
                    "avg": iteration_duration.get("avg"),
                    "min": iteration_duration.get("min"),
                    "max": iteration_duration.get("max"),
                },
            },
            "summary": summary_data,
            "root_group": summary_data.get("root_group", {}),  # Include test checks and groups
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
                "k6", "version",
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
                "k6", "version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, _ = await process.communicate()

            if process.returncode == 0:
                return stdout.decode().strip()

            return "Unknown"

        except Exception:
            return "Error getting version"