"""
Repository Interfaces for LoadTester
Domain layer interfaces for data access abstraction
"""

from abc import ABC, abstractmethod
from typing import List, Optional

from loadtester.domain.entities.domain_entities import (
    API, Endpoint, Job, TestExecution, TestResult, TestScenario
)


class APIRepositoryInterface(ABC):
    """Interface for API repository."""
    
    @abstractmethod
    async def create(self, api: API) -> API:
        """Create a new API."""
        pass
    
    @abstractmethod
    async def get_by_id(self, api_id: int) -> Optional[API]:
        """Get API by ID."""
        pass
    
    @abstractmethod
    async def get_by_name(self, name: str) -> Optional[API]:
        """Get API by name."""
        pass
    
    @abstractmethod
    async def get_all(self) -> List[API]:
        """Get all APIs."""
        pass
    
    @abstractmethod
    async def update(self, api: API) -> API:
        """Update API."""
        pass
    
    @abstractmethod
    async def delete(self, api_id: int) -> bool:
        """Delete API."""
        pass


class EndpointRepositoryInterface(ABC):
    """Interface for Endpoint repository."""
    
    @abstractmethod
    async def create(self, endpoint: Endpoint) -> Endpoint:
        """Create a new endpoint."""
        pass
    
    @abstractmethod
    async def get_by_id(self, endpoint_id: int) -> Optional[Endpoint]:
        """Get endpoint by ID."""
        pass
    
    @abstractmethod
    async def get_by_api_id(self, api_id: int) -> List[Endpoint]:
        """Get all endpoints for an API."""
        pass
    
    @abstractmethod
    async def get_by_path_and_method(self, path: str, method: str) -> Optional[Endpoint]:
        """Get endpoint by path and HTTP method."""
        pass
    
    @abstractmethod
    async def update(self, endpoint: Endpoint) -> Endpoint:
        """Update endpoint."""
        pass
    
    @abstractmethod
    async def delete(self, endpoint_id: int) -> bool:
        """Delete endpoint."""
        pass


class TestScenarioRepositoryInterface(ABC):
    """Interface for TestScenario repository."""
    
    @abstractmethod
    async def create(self, scenario: TestScenario) -> TestScenario:
        """Create a new test scenario."""
        pass
    
    @abstractmethod
    async def get_by_id(self, scenario_id: int) -> Optional[TestScenario]:
        """Get test scenario by ID."""
        pass
    
    @abstractmethod
    async def get_by_endpoint_id(self, endpoint_id: int) -> List[TestScenario]:
        """Get all scenarios for an endpoint."""
        pass
    
    @abstractmethod
    async def get_by_job_id(self, job_id: str) -> List[TestScenario]:
        """Get all scenarios for a job."""
        pass
    
    @abstractmethod
    async def update(self, scenario: TestScenario) -> TestScenario:
        """Update test scenario."""
        pass
    
    @abstractmethod
    async def delete(self, scenario_id: int) -> bool:
        """Delete test scenario."""
        pass


class TestExecutionRepositoryInterface(ABC):
    """Interface for TestExecution repository."""
    
    @abstractmethod
    async def create(self, execution: TestExecution) -> TestExecution:
        """Create a new test execution."""
        pass
    
    @abstractmethod
    async def get_by_id(self, execution_id: int) -> Optional[TestExecution]:
        """Get test execution by ID."""
        pass
    
    @abstractmethod
    async def get_by_scenario_id(self, scenario_id: int) -> List[TestExecution]:
        """Get all executions for a scenario."""
        pass
    
    @abstractmethod
    async def get_by_job_id(self, job_id: str) -> List[TestExecution]:
        """Get all executions for a job."""
        pass
    
    @abstractmethod
    async def get_running_executions(self) -> List[TestExecution]:
        """Get all currently running executions."""
        pass
    
    @abstractmethod
    async def update(self, execution: TestExecution) -> TestExecution:
        """Update test execution."""
        pass
    
    @abstractmethod
    async def delete(self, execution_id: int) -> bool:
        """Delete test execution."""
        pass


class TestResultRepositoryInterface(ABC):
    """Interface for TestResult repository."""
    
    @abstractmethod
    async def create(self, result: TestResult) -> TestResult:
        """Create a new test result."""
        pass
    
    @abstractmethod
    async def get_by_id(self, result_id: int) -> Optional[TestResult]:
        """Get test result by ID."""
        pass
    
    @abstractmethod
    async def get_by_execution_id(self, execution_id: int) -> Optional[TestResult]:
        """Get test result by execution ID."""
        pass
    
    @abstractmethod
    async def get_by_job_id(self, job_id: str) -> List[TestResult]:
        """Get all results for a job."""
        pass
    
    @abstractmethod
    async def update(self, result: TestResult) -> TestResult:
        """Update test result."""
        pass
    
    @abstractmethod
    async def delete(self, result_id: int) -> bool:
        """Delete test result."""
        pass


class JobRepositoryInterface(ABC):
    """Interface for Job repository."""
    
    @abstractmethod
    async def create(self, job: Job) -> Job:
        """Create a new job."""
        pass
    
    @abstractmethod
    async def get_by_id(self, job_id: str) -> Optional[Job]:
        """Get job by ID."""
        pass
    
    @abstractmethod
    async def get_pending_jobs(self) -> List[Job]:
        """Get all pending jobs."""
        pass
    
    @abstractmethod
    async def get_running_jobs(self) -> List[Job]:
        """Get all running jobs."""
        pass
    
    @abstractmethod
    async def get_jobs_by_type(self, job_type: str) -> List[Job]:
        """Get jobs by type."""
        pass
    
    @abstractmethod
    async def update(self, job: Job) -> Job:
        """Update job."""
        pass
    
    @abstractmethod
    async def delete(self, job_id: str) -> bool:
        """Delete job."""
        pass
    
    @abstractmethod
    async def cleanup_old_jobs(self, days: int = 7) -> int:
        """Clean up old completed jobs and return count of deleted jobs."""
        pass