"""
Script to reprocess K6 results for a job that completed without saving results.
This script reads the existing K6 results file and saves the metrics to the database.
"""
import asyncio
import json
import sys
from pathlib import Path

# Add loadtester to path
sys.path.insert(0, str(Path(__file__).parent))

from loadtester.infrastructure.database.database_connection import DatabaseManager
from loadtester.infrastructure.repositories.test_execution_repository import TestExecutionRepository
from loadtester.infrastructure.repositories.test_result_repository import TestResultRepository
from loadtester.domain.entities.domain_entities import TestResult
from loadtester.settings import Settings


async def reprocess_job_results(job_id: str, execution_id: int, results_file: str):
    """Reprocess K6 results and save to database."""

    # Read the summary file
    summary_file = f"{results_file}.summary"
    with open(summary_file, 'r') as f:
        summary_data = json.load(f)

    metrics = summary_data.get("metrics", {})

    # Extract metrics
    http_req_duration = metrics.get("http_req_duration", {})
    http_reqs = metrics.get("http_reqs", {})
    http_req_failed = metrics.get("http_req_failed", {})
    data_sent = metrics.get("data_sent", {})
    data_received = metrics.get("data_received", {})

    # Calculate success rate
    total_requests = http_reqs.get("count", 0)
    failed_count = http_req_failed.get("passes", 0)  # In summary, 'passes' is failed count
    failure_rate = http_req_failed.get("value", 0)  # 0-1 range

    success_rate = (1 - failure_rate) * 100 if failure_rate is not None else 0
    successful_requests = total_requests - failed_count if failed_count else total_requests

    print(f"\n=== Metrics for job {job_id} ===")
    print(f"Total requests: {total_requests}")
    print(f"Failed requests: {failed_count}")
    print(f"Success rate: {success_rate:.2f}%")
    print(f"Avg response time: {http_req_duration.get('avg')}")
    print(f"P95 response time: {http_req_duration.get('p(95)')}")
    print(f"Max response time: {http_req_duration.get('max')}")

    # Create TestResult
    result = TestResult(
        execution_id=execution_id,
        avg_response_time_ms=http_req_duration.get("avg"),
        p95_response_time_ms=http_req_duration.get("p(95)"),
        p99_response_time_ms=http_req_duration.get("p(99)"),
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

    # Save to database
    settings = Settings()
    db_manager = DatabaseManager(settings.database_url)

    async with db_manager.get_session_context() as session:
        result_repo = TestResultRepository(session=session)
        saved_result = await result_repo.create(result)
        print(f"\n✅ Result saved with ID: {saved_result.result_id}")
        return saved_result


if __name__ == "__main__":
    # Job 5dc9b077-cb68-41ba-9434-50ddaa81f690
    # Execution ID: 23 (from results_23.json)
    job_id = "5dc9b077-cb68-41ba-9434-50ddaa81f690"
    execution_id = 23
    results_file = "/app/k6_results/results_23.json"

    asyncio.run(reprocess_job_results(job_id, execution_id, results_file))
