"""
Load Test Service - Core Business Logic
Main orchestrator for load testing operations
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Optional
from uuid import uuid4

from loadtester.domain.entities.domain_entities import (
    API, AuthConfig, DegradationDetectionResult, Endpoint, ExecutionStatus,
    Job, JobStatus, LoadTestConfiguration, TestExecution, TestResult,
    TestScenario
)
from loadtester.domain.interfaces.service_interfaces import (
    K6RunnerServiceInterface, K6ScriptGeneratorServiceInterface,
    MockDataGeneratorServiceInterface, OpenAPIParserServiceInterface,
    ReportGeneratorServiceInterface
)
from loadtester.domain.interfaces.domain_interfaces import (
    APIRepositoryInterface, EndpointRepositoryInterface,
    JobRepositoryInterface, TestExecutionRepositoryInterface,
    TestResultRepositoryInterface, TestScenarioRepositoryInterface
)
from loadtester.shared.exceptions.domain_exceptions import (
    InvalidConfigurationError, LoadTestExecutionError,
    ResourceNotFoundError
)

logger = logging.getLogger(__name__)


class LoadTestService:
    """Core service for load testing operations."""
    
    def __init__(
        self,
        api_repository: APIRepositoryInterface,
        endpoint_repository: EndpointRepositoryInterface,
        scenario_repository: TestScenarioRepositoryInterface,
        execution_repository: TestExecutionRepositoryInterface,
        result_repository: TestResultRepositoryInterface,
        job_repository: JobRepositoryInterface,
        openapi_parser: OpenAPIParserServiceInterface,
        mock_generator: MockDataGeneratorServiceInterface,
        k6_generator: K6ScriptGeneratorServiceInterface,
        k6_runner: K6RunnerServiceInterface,
        report_generator: ReportGeneratorServiceInterface,
        degradation_settings: Dict,
    ):
        self.api_repository = api_repository
        self.endpoint_repository = endpoint_repository
        self.scenario_repository = scenario_repository
        self.execution_repository = execution_repository
        self.result_repository = result_repository
        self.job_repository = job_repository
        self.openapi_parser = openapi_parser
        self.mock_generator = mock_generator
        self.k6_generator = k6_generator
        self.k6_runner = k6_runner
        self.report_generator = report_generator
        self.degradation_settings = degradation_settings
        
    async def create_load_test_job(self, config: LoadTestConfiguration) -> Job:
        """Create a new load test job."""
        logger.info("Creating new load test job")
        
        # Validate configuration
        errors = config.validate()
        if errors:
            raise InvalidConfigurationError(f"Configuration errors: {', '.join(errors)}")
        
        # Check if we can run concurrent jobs
        running_jobs = await self.job_repository.get_running_jobs()
        max_concurrent = self.degradation_settings.get("max_concurrent_jobs", 1)
        
        if len(running_jobs) >= max_concurrent:
            raise LoadTestExecutionError(
                f"Maximum concurrent jobs ({max_concurrent}) reached. "
                f"Currently running: {len(running_jobs)}"
            )
        
        # Create job
        job = Job(
            job_id=str(uuid4()),
            job_type="load_test",
            status=JobStatus.PENDING,
            callback_url=config.callback_url,
            created_at=datetime.utcnow(),
        )
        
        await self.job_repository.create(job)
        logger.info(f"Created job {job.job_id}")
        
        return job
    
    async def execute_load_test(self, job_id: str, config: LoadTestConfiguration) -> None:
        """Execute load test asynchronously."""
        logger.info(f"Starting load test execution for job {job_id}")
        
        job = await self.job_repository.get_by_id(job_id)
        if not job:
            raise ResourceNotFoundError(f"Job {job_id} not found")
        
        try:
            # Mark job as started
            job.start()
            await self.job_repository.update(job)
            
            # Phase 1: Parse OpenAPI spec (10% progress)
            await self._update_job_progress(job, 5.0, "Parsing OpenAPI specification")
            api, endpoints = await self._parse_and_create_api(config)
            
            await self._update_job_progress(job, 10.0, "OpenAPI parsed successfully")
            
            # Phase 2: Generate test scenarios (20% progress)
            await self._update_job_progress(job, 15.0, "Generating test scenarios")
            scenarios = await self._generate_test_scenarios(endpoints, config)
            
            await self._update_job_progress(job, 20.0, f"Generated {len(scenarios)} test scenarios")
            
            # Phase 3: Execute scenarios (20% - 80% progress)
            await self._update_job_progress(job, 25.0, "Starting test execution")
            results = await self._execute_test_scenarios(job, scenarios)
            
            await self._update_job_progress(job, 80.0, "Test execution completed")
            
            # Phase 4: Generate report (80% - 95% progress)
            await self._update_job_progress(job, 85.0, "Generating report")
            report_path = await self._generate_final_report(job, results)
            
            await self._update_job_progress(job, 95.0, "Report generated")
            
            # Phase 5: Finalize (95% - 100% progress)
            job.finish({
                "report_path": report_path,
                "total_scenarios": len(scenarios),
                "total_results": len(results),
                "api_id": api.api_id,
            })
            
            await self.job_repository.update(job)
            await self._update_job_progress(job, 100.0, "Load test completed")
            
            logger.info(f"Load test job {job_id} completed successfully")
            
        except Exception as e:
            logger.error(f"Load test job {job_id} failed: {str(e)}")
            job.fail(str(e))
            await self.job_repository.update(job)
            raise
    
    async def get_job_status(self, job_id: str) -> Dict:
        """Get job status and progress."""
        job = await self.job_repository.get_by_id(job_id)
        if not job:
            raise ResourceNotFoundError(f"Job {job_id} not found")
        
        status_response = {
            "job_id": job.job_id,
            "status": job.status.value,
            "progress": job.progress_percentage,
            "created_at": job.created_at.isoformat() if job.created_at else None,
            "started_at": job.started_at.isoformat() if job.started_at else None,
            "finished_at": job.finished_at.isoformat() if job.finished_at else None,
        }
        
        if job.status == JobStatus.FINISHED:
            if job.result_data and "report_path" in job.result_data:
                status_response["report_url"] = f"/api/v1/report/{job_id}"
        
        if job.status == JobStatus.FAILED:
            status_response["error_message"] = job.error_message
        
        return status_response
    
    async def _parse_and_create_api(self, config: LoadTestConfiguration) -> tuple[API, List[Endpoint]]:
        """Parse OpenAPI spec and create API/Endpoint entities."""
        logger.info("Parsing OpenAPI specification")
        
        # Validate and parse spec
        is_valid = await self.openapi_parser.validate_spec(config.api_spec)
        if not is_valid:
            raise InvalidConfigurationError("Invalid OpenAPI specification")
        
        parsed_spec = await self.openapi_parser.parse_openapi_spec(config.api_spec)
        available_endpoints = await self.openapi_parser.extract_endpoints(parsed_spec)
        
        # Create API entity
        api = API(
            api_name=parsed_spec.get("info", {}).get("title", "Untitled API"),
            base_url=self._extract_base_url(parsed_spec),
            description=parsed_spec.get("info", {}).get("description"),
            created_at=datetime.utcnow(),
        )
        
        api = await self.api_repository.create(api)
        
        # Create endpoint entities for selected endpoints
        endpoints = []
        selected_map = {(ep["path"], ep["method"]): ep for ep in config.selected_endpoints}
        
        for available_ep in available_endpoints:
            path = available_ep["path"]
            method = available_ep["method"].upper()
            
            if (path, method) in selected_map:
                selected_config = selected_map[(path, method)]
                
                # Get endpoint schema
                schema = await self.openapi_parser.get_endpoint_schema(
                    parsed_spec, path, method
                )

                endpoint = Endpoint(
                    api_id=api.api_id,
                    endpoint_name=f"{method} {path}",
                    http_method=method,
                    endpoint_path=path,
                    description=available_ep.get("description"),
                    expected_volumetry=selected_config.get("expected_volumetry"),
                    expected_concurrent_users=selected_config.get("expected_concurrent_users"),
                    auth_config=self._create_auth_config(selected_config, config.global_auth),
                    timeout_ms=selected_config.get("timeout_ms", 30000),
                    schema=schema,  # Store the schema for mock data generation
                    created_at=datetime.utcnow(),
                )
                
                endpoint = await self.endpoint_repository.create(endpoint)
                endpoints.append(endpoint)
        
        logger.info(f"Created API with {len(endpoints)} endpoints")
        return api, endpoints
    
    async def _generate_test_scenarios(
        self, 
        endpoints: List[Endpoint], 
        config: LoadTestConfiguration
    ) -> List[TestScenario]:
        """Generate test scenarios for each endpoint."""
        logger.info("Generating test scenarios")
        
        scenarios = []
        
        for endpoint in endpoints:
            # Generate mock data if needed
            test_data = await self._generate_or_load_test_data(endpoint, config)
            
            # Create scenarios with incremental load
            endpoint_scenarios = await self._create_incremental_scenarios(endpoint, test_data)
            scenarios.extend(endpoint_scenarios)
        
        logger.info(f"Generated {len(scenarios)} total scenarios")
        return scenarios
    
    async def _create_incremental_scenarios(
        self,
        endpoint: Endpoint,
        test_data: List[Dict]
    ) -> List[TestScenario]:
        """Create incremental load scenarios for an endpoint.

        Scenarios are created at specific percentages of expected load:
        25% (warm-up), 50%, 75%, 100%, 150%, 200%
        """
        scenarios = []

        # Define load percentages for scenarios (including warm-up)
        # 25% is warm-up to initialize connections, caches, etc.
        load_percentages = [25, 50, 75, 100, 150, 200]

        for load_percentage in load_percentages:
            # Calculate users and volumetry for this load percentage
            current_users = max(1, int(endpoint.expected_concurrent_users * (load_percentage / 100)))
            current_volumetry = max(1, int(endpoint.expected_volumetry * (load_percentage / 100)))

            # Mark warm-up scenario
            is_warmup = (load_percentage == 25)
            scenario_name = f"{endpoint.endpoint_name} - {load_percentage}% carga esperada ({current_users} users)"
            if is_warmup:
                scenario_name = f"{endpoint.endpoint_name} - WARM-UP {load_percentage}% ({current_users} users)"

            scenario = TestScenario(
                endpoint_id=endpoint.endpoint_id,
                scenario_name=scenario_name,
                description=f"{'Warm-up: ' if is_warmup else ''}Load test at {load_percentage}% of expected load: {current_users} users, {current_volumetry} req/min",
                target_volumetry=current_volumetry,
                concurrent_users=current_users,
                duration_seconds=self.degradation_settings.get("default_test_duration", 60),
                ramp_up_seconds=10,
                ramp_down_seconds=10,
                test_data=test_data,
                created_at=datetime.utcnow(),
            )

            scenario = await self.scenario_repository.create(scenario)
            scenarios.append(scenario)

        return scenarios
    
    async def _execute_test_scenarios(
        self, 
        job: Job, 
        scenarios: List[TestScenario]
    ) -> List[TestResult]:
        """Execute test scenarios and collect results."""
        logger.info(f"Executing {len(scenarios)} test scenarios")
        
        results = []
        total_scenarios = len(scenarios)
        base_progress = 25.0  # Starting from 25%
        progress_per_scenario = 55.0 / total_scenarios  # 55% total for execution (25% to 80%)
        
        baseline_response_time = None
        
        for i, scenario in enumerate(scenarios):
            current_progress = base_progress + (i * progress_per_scenario)
            await self._update_job_progress(
                job, 
                current_progress, 
                f"Executing scenario {i+1}/{total_scenarios}"
            )
            
            # Execute scenario
            result = await self._execute_single_scenario(scenario)
            
            if result:
                results.append(result)
                
                # Set baseline from first successful result
                if baseline_response_time is None and result.avg_response_time_ms:
                    baseline_response_time = result.avg_response_time_ms
                
                # Check for degradation
                if await self._should_stop_due_to_degradation(result, baseline_response_time):
                    logger.info(f"Stopping scenarios due to degradation at scenario {i+1}")
                    break
        
        logger.info(f"Completed execution with {len(results)} results")
        return results
    
    async def _execute_single_scenario(self, scenario: TestScenario) -> Optional[TestResult]:
        """Execute a single test scenario."""
        logger.info(f"Executing scenario: {scenario.scenario_name}")
        
        # Create execution record
        execution = TestExecution(
            scenario_id=scenario.scenario_id,
            execution_name=f"Execution of {scenario.scenario_name}",
            status=ExecutionStatus.PENDING,
            executed_by="load_test_service",
        )
        
        execution = await self.execution_repository.create(execution)
        
        try:
            # Mark as running
            execution.status = ExecutionStatus.RUNNING
            execution.start_time = datetime.utcnow()
            await self.execution_repository.update(execution)
            
            # Get endpoint for script generation
            endpoint = await self.endpoint_repository.get_by_id(scenario.endpoint_id)
            if not endpoint:
                raise ResourceNotFoundError(f"Endpoint {scenario.endpoint_id} not found")

            # Get API for base URL
            api = await self.api_repository.get_by_id(endpoint.api_id)
            if not api:
                raise ResourceNotFoundError(f"API {endpoint.api_id} not found")

            # Attach API to endpoint for K6 script generation
            endpoint.api = api

            # Generate K6 script
            scenario_config = {
                "concurrent_users": scenario.concurrent_users,
                "target_volumetry": scenario.target_volumetry,
                "duration": scenario.duration_seconds,
                "ramp_up": scenario.ramp_up_seconds,
                "ramp_down": scenario.ramp_down_seconds,
            }

            k6_script = await self.k6_generator.generate_k6_script(
                endpoint, scenario.test_data or [], scenario_config
            )
            
            execution.k6_script_used = k6_script
            await self.execution_repository.update(execution)
            
            # Execute K6 script
            k6_results = await self.k6_runner.execute_k6_script(
                script_content=k6_script,
                execution_id=execution.execution_id
            )
            
            # Mark execution as finished
            execution.status = ExecutionStatus.FINISHED
            execution.end_time = datetime.utcnow()
            execution.actual_duration_seconds = (
                execution.end_time - execution.start_time
            ).total_seconds()
            execution.execution_logs = json.dumps(k6_results.get("logs", []))
            
            await self.execution_repository.update(execution)
            
            # Create test result
            result = self._parse_k6_results_to_test_result(k6_results, execution.execution_id)
            result = await self.result_repository.create(result)
            
            logger.info(f"Scenario execution completed: {scenario.scenario_name}")
            return result
            
        except Exception as e:
            logger.error(f"Scenario execution failed: {str(e)}")
            execution.status = ExecutionStatus.FAILED
            execution.end_time = datetime.utcnow()
            execution.execution_logs = str(e)
            await self.execution_repository.update(execution)
            return None
    
    async def _should_stop_due_to_degradation(
        self, 
        result: TestResult, 
        baseline_response_time: Optional[float]
    ) -> bool:
        """Check if we should stop due to degradation."""
        if not result:
            return True
        
        # Check error rate
        error_threshold = self.degradation_settings["stop_error_threshold"]
        if result.error_rate_percent > (error_threshold * 100):
            logger.info(f"Stopping due to high error rate: {result.error_rate_percent}%")
            return True
        
        # Check response time degradation
        if baseline_response_time and result.avg_response_time_ms:
            multiplier = self.degradation_settings["degradation_response_time_multiplier"]
            if result.avg_response_time_ms > (baseline_response_time * multiplier):
                logger.info(f"Stopping due to response time degradation: "
                           f"{result.avg_response_time_ms}ms vs baseline {baseline_response_time}ms")
                return True
        
        return False
    
    async def _generate_final_report(self, job: Job, results: List[TestResult]) -> str:
        """Generate final PDF report."""
        logger.info("Generating final report")

        # Calculate test duration (use current time since job hasn't been marked as finished yet)
        test_duration = 0
        if job.started_at:
            duration_delta = datetime.utcnow() - job.started_at
            test_duration = int(duration_delta.total_seconds())
            logger.info(f"Test duration calculated: {test_duration} seconds (from {job.started_at} to now)")
        else:
            logger.warning(f"Cannot calculate test duration - started_at is None")

        # Group results by endpoint and collect endpoint details
        endpoint_details = {}
        for result in results:
            if result.execution_id:
                try:
                    execution = await self.execution_repository.get_by_id(result.execution_id)
                    if execution and execution.scenario_id:
                        scenario = await self.scenario_repository.get_by_id(execution.scenario_id)
                        if scenario and scenario.endpoint_id:
                            endpoint = await self.endpoint_repository.get_by_id(scenario.endpoint_id)
                            if endpoint:
                                endpoint_key = f"{endpoint.http_method}_{endpoint.endpoint_path}"

                                if endpoint_key not in endpoint_details:
                                    # Get API info for base URL
                                    api = None
                                    if endpoint.api_id:
                                        api = await self.api_repository.get_by_id(endpoint.api_id)

                                    endpoint_details[endpoint_key] = {
                                        'endpoint': endpoint,
                                        'api': api,
                                        'scenarios': []
                                    }

                                # Add scenario result
                                endpoint_details[endpoint_key]['scenarios'].append({
                                    'scenario': scenario,
                                    'execution': execution,
                                    'result': result
                                })
                except Exception as e:
                    logger.warning(f"Could not get endpoint for result {result.result_id}: {e}")

        job_info = {
            "job_id": job.job_id,
            "created_at": job.created_at,
            "started_at": job.started_at,
            "finished_at": job.finished_at,
            "total_scenarios": len(results),
            "total_endpoints": len(endpoint_details),
            "test_duration": test_duration,
            "endpoint_details": endpoint_details,  # Pass structured endpoint data
        }

        report_path = await self.report_generator.generate_technical_report(results, job_info)
        logger.info(f"Report generated: {report_path}")

        return report_path
    
    def _extract_base_url(self, parsed_spec: Dict) -> str:
        """Extract base URL from OpenAPI spec."""
        # Try to get from servers (OpenAPI 3.0+)
        if "servers" in parsed_spec and parsed_spec["servers"]:
            server_url = parsed_spec["servers"][0].get("url", "")

            # Check if the URL is relative (starts with /)
            if server_url.startswith("/"):
                # It's a relative URL, need to construct full URL
                # Try to get host from spec info or use a default
                logger.warning(f"Server URL is relative: {server_url}. Need to add host.")

                # Check if there's an 'x-server-url' extension or similar
                if "x-server-url" in parsed_spec.get("info", {}):
                    base_host = parsed_spec["info"]["x-server-url"]
                    full_url = f"{base_host.rstrip('/')}{server_url}"
                    logger.info(f"Constructed full URL from x-server-url: {full_url}")
                    return full_url

                # If spec has externalDocs with a URL, check if it's a known API
                if "externalDocs" in parsed_spec:
                    ext_url = parsed_spec["externalDocs"].get("url", "")
                    if ext_url:
                        from urllib.parse import urlparse
                        parsed = urlparse(ext_url)

                        # Special handling for known APIs (Petstore)
                        if "swagger.io" in ext_url and server_url.startswith("/api/v"):
                            # This is likely the Petstore API
                            version = server_url.split("/")[2] if len(server_url.split("/")) > 2 else "v3"
                            if version == "v2":
                                full_url = f"https://petstore.swagger.io{server_url}"
                            else:  # v3 or other
                                full_url = f"https://petstore3.swagger.io{server_url}"
                            logger.info(f"Detected Petstore API, using correct server: {full_url}")
                            return full_url

                        # For other APIs, try to extract host from external docs
                        if parsed.scheme and parsed.netloc:
                            base_host = f"{parsed.scheme}://{parsed.netloc}"
                            full_url = f"{base_host}{server_url}"
                            logger.info(f"Constructed full URL from externalDocs: {full_url}")
                            return full_url

                # Last resort: return as-is and let it be handled later
                logger.warning(f"Could not determine full host, returning relative URL: {server_url}")
                return server_url

            # URL is absolute
            logger.info(f"Extracted absolute base URL: {server_url}")
            return server_url

        # Fallback to host + basePath (OpenAPI 2.0)
        host = parsed_spec.get("host", "")
        schemes = parsed_spec.get("schemes", ["https"])
        base_path = parsed_spec.get("basePath", "")

        if host:
            full_url = f"{schemes[0]}://{host}{base_path}"
            logger.info(f"Constructed base URL from host: {full_url}")
            return full_url

        logger.warning("Could not extract base URL from spec")
        return ""
    
    def _create_auth_config(
        self, 
        endpoint_config: Dict, 
        global_auth: Optional[AuthConfig]
    ) -> Optional[AuthConfig]:
        """Create auth config for endpoint."""
        # Endpoint-specific auth takes precedence
        if "auth" in endpoint_config and endpoint_config["auth"] is not None:
            auth_data = endpoint_config["auth"]
            return AuthConfig(
                auth_type=auth_data.get("type"),
                token=auth_data.get("token"),
                api_key=auth_data.get("api_key"),
                header_name=auth_data.get("header_name"),
                query_param_name=auth_data.get("query_param_name"),
            )
        
        # Fallback to global auth
        return global_auth
    
    async def _generate_or_load_test_data(
        self,
        endpoint: Endpoint,
        config: LoadTestConfiguration
    ) -> List[Dict]:
        """Generate or load test data for endpoint."""
        # Calculate how many unique data records we need
        # For POST/PUT/PATCH endpoints with potential uniqueness constraints (like email)
        # we need enough data for the maximum load scenario (200% load)
        # Formula: (volumetry * 2) * (test_duration_seconds / 60) + buffer
        # With 60s test duration: (volumetry * 2) * 1 + 50% buffer
        required_count = max(100, int(endpoint.expected_volumetry * 2 * 1.5))
        logger.info(f"Calculating mock data count for {endpoint.endpoint_name}: "
                   f"volumetry={endpoint.expected_volumetry}, required_count={required_count}")

        # Check if endpoint has custom data file
        for selected_ep in config.selected_endpoints:
            if (selected_ep.get("path") == endpoint.endpoint_path and
                selected_ep.get("method") == endpoint.http_method):

                # Only load from file if data_file has a real value (not None, not empty)
                if selected_ep.get("data_file"):
                    # Load custom data (implement file loading)
                    return await self._load_test_data_file(selected_ep["data_file"])
                elif selected_ep.get("use_mock_data", True):
                    # Generate mock data with the endpoint's schema
                    return await self.mock_generator.generate_mock_data(
                        endpoint, endpoint.schema or {}, count=required_count
                    )

        # Default: generate mock data with the endpoint's schema
        return await self.mock_generator.generate_mock_data(endpoint, endpoint.schema or {}, count=required_count)
    
    async def _load_test_data_file(self, file_path: str) -> List[Dict]:
        """Load test data from file."""
        # TODO: Implement file loading logic
        # This would handle CSV, JSON, Excel files
        return []
    
    def _parse_k6_results_to_test_result(
        self,
        k6_results: Dict,
        execution_id: int
    ) -> TestResult:
        """Parse K6 results into TestResult entity."""
        metrics = k6_results.get("metrics", {})

        # Extract metrics with safe defaults
        http_req_duration = metrics.get("http_req_duration", {})
        http_reqs = metrics.get("http_reqs", {})
        http_req_failed = metrics.get("http_req_failed", {})
        data_sent = metrics.get("data_sent", {})
        data_received = metrics.get("data_received", {})

        # Calculate success rate (failure rate is in 'value' or 'rate', ranging 0-1)
        total_requests = http_reqs.get("count", 0)
        failed_count = http_req_failed.get("count", 0)
        failure_rate = http_req_failed.get("rate", 0)  # 0-1 range

        # Success rate is (1 - failure_rate) * 100
        success_rate = (1 - failure_rate) * 100 if failure_rate is not None else 0

        # If we have failed_count, calculate successful requests
        successful_requests = total_requests - failed_count if failed_count else total_requests

        return TestResult(
            execution_id=execution_id,
            avg_response_time_ms=http_req_duration.get("avg"),
            p95_response_time_ms=http_req_duration.get("p(95)"),
            p99_response_time_ms=http_req_duration.get("p(99)"),  # May be None
            min_response_time_ms=http_req_duration.get("min"),
            max_response_time_ms=http_req_duration.get("max"),
            total_requests=total_requests,
            successful_requests=successful_requests,
            failed_requests=failed_count,
            success_rate_percent=success_rate,
            requests_per_second=http_reqs.get("rate"),
            data_sent_kb=data_sent.get("count", 0) / 1024 if data_sent.get("count") else 0,
            data_received_kb=data_received.get("count", 0) / 1024 if data_received.get("count") else 0,
        )
    
    async def _update_job_progress(
        self, 
        job: Job, 
        percentage: float, 
        message: Optional[str] = None
    ) -> None:
        """Update job progress."""
        job.update_progress(percentage)
        await self.job_repository.update(job)
        
        if message:
            logger.info(f"Job {job.job_id}: {message} ({percentage:.1f}%)")

    async def cancel_job(self, job_id: str) -> bool:
        """Cancel a specific job."""
        try:
            job = await self.job_repository.get_by_id(job_id)

            if not job:
                logger.warning(f"Job {job_id} not found")
                return False

            # Only cancel if job is PENDING or RUNNING
            if job.status not in [JobStatus.PENDING, JobStatus.RUNNING]:
                logger.warning(f"Job {job_id} is {job.status}, cannot cancel")
                return False

            # Update job status to FAILED with cancellation message
            job.status = JobStatus.FAILED
            job.error_message = "Job cancelled by user"
            job.end_time = datetime.utcnow()

            await self.job_repository.update(job)
            logger.info(f"Job {job_id} cancelled successfully")
            return True

        except Exception as e:
            logger.error(f"Error cancelling job {job_id}: {str(e)}")
            return False

    async def cancel_all_running_jobs(self) -> int:
        """Cancel all running or pending jobs."""
        try:
            # Get all jobs with RUNNING or PENDING status
            all_jobs = await self.job_repository.get_all()
            active_jobs = [
                job for job in all_jobs
                if job.status in [JobStatus.PENDING, JobStatus.RUNNING]
            ]

            cancelled_count = 0
            for job in active_jobs:
                job.status = JobStatus.FAILED
                job.error_message = "Job cancelled by user (bulk cancellation)"
                job.end_time = datetime.utcnow()
                await self.job_repository.update(job)
                cancelled_count += 1

            logger.info(f"Cancelled {cancelled_count} running/pending jobs")
            return cancelled_count

        except Exception as e:
            logger.error(f"Error cancelling all jobs: {str(e)}")
            return 0
