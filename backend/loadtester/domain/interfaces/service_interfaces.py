"""
AI Services Interfaces for LoadTester
Domain layer interfaces for AI service abstraction
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional

from loadtester.domain.entities.domain_entities import Endpoint, TestResult


class OpenAPIParserServiceInterface(ABC):
    """Interface for OpenAPI parsing service."""
    
    @abstractmethod
    async def parse_openapi_spec(self, spec_content: str) -> Dict:
        """Parse OpenAPI specification and return structured data."""
        pass
    
    @abstractmethod
    async def extract_endpoints(self, parsed_spec: Dict) -> List[Dict]:
        """Extract endpoints information from parsed spec."""
        pass
    
    @abstractmethod
    async def validate_spec(self, spec_content: str) -> bool:
        """Validate OpenAPI specification format."""
        pass
    
    @abstractmethod
    async def get_endpoint_schema(self, parsed_spec: Dict, path: str, method: str) -> Optional[Dict]:
        """Get schema for specific endpoint."""
        pass


class MockDataGeneratorServiceInterface(ABC):
    """Interface for mock data generation service."""
    
    @abstractmethod
    async def generate_mock_data(
        self, 
        endpoint: Endpoint, 
        schema: Dict, 
        count: int = 100
    ) -> List[Dict]:
        """Generate mock data for endpoint based on schema."""
        pass
    
    @abstractmethod
    async def generate_path_parameters(self, path: str, schema: Dict) -> Dict:
        """Generate mock path parameters."""
        pass
    
    @abstractmethod
    async def generate_query_parameters(self, schema: Dict) -> Dict:
        """Generate mock query parameters."""
        pass
    
    @abstractmethod
    async def generate_request_body(self, schema: Dict) -> Dict:
        """Generate mock request body."""
        pass
    
    @abstractmethod
    async def validate_generated_data(self, data: Dict, schema: Dict) -> bool:
        """Validate generated data against schema."""
        pass


class K6ScriptGeneratorServiceInterface(ABC):
    """Interface for K6 script generation service."""
    
    @abstractmethod
    async def generate_k6_script(
        self, 
        endpoint: Endpoint, 
        test_data: List[Dict], 
        scenario_config: Dict
    ) -> str:
        """Generate K6 script for load testing."""
        pass
    
    @abstractmethod
    async def generate_scenario_options(
        self, 
        concurrent_users: int, 
        duration: int, 
        ramp_up: int, 
        ramp_down: int
    ) -> Dict:
        """Generate K6 scenario options."""
        pass
    
    @abstractmethod
    async def validate_script(self, script: str) -> bool:
        """Validate generated K6 script syntax."""
        pass


class ReportGeneratorServiceInterface(ABC):
    """Interface for report generation service."""
    
    @abstractmethod
    async def generate_technical_report(
        self, 
        test_results: List[TestResult], 
        job_info: Dict
    ) -> str:
        """Generate technical PDF report."""
        pass
    
    @abstractmethod
    async def generate_executive_summary(
        self, 
        test_results: List[TestResult], 
        job_info: Dict
    ) -> Dict:
        """Generate executive summary for report."""
        pass
    
    @abstractmethod
    async def analyze_performance_trends(self, test_results: List[TestResult]) -> Dict:
        """Analyze performance trends across test results."""
        pass
    
    @abstractmethod
    async def detect_degradation_points(self, test_results: List[TestResult]) -> List[Dict]:
        """Detect degradation points in test results."""
        pass


class AIClientInterface(ABC):
    """Interface for AI client implementations."""
    
    @abstractmethod
    async def chat_completion(
        self, 
        messages: List[Dict[str, str]], 
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None
    ) -> str:
        """Get chat completion from AI service."""
        pass
    
    @abstractmethod
    async def is_available(self) -> bool:
        """Check if AI service is available."""
        pass
    
    @abstractmethod
    def get_service_name(self) -> str:
        """Get AI service name."""
        pass


class K6RunnerServiceInterface(ABC):
    """Interface for K6 execution service."""
    
    @abstractmethod
    async def execute_k6_script(
        self, 
        script_path: str, 
        output_path: str,
        options: Optional[Dict] = None
    ) -> Dict:
        """Execute K6 script and return results."""
        pass
    
    @abstractmethod
    async def parse_k6_results(self, results_path: str) -> Dict:
        """Parse K6 execution results."""
        pass
    
    @abstractmethod
    async def is_k6_available(self) -> bool:
        """Check if K6 is available for execution."""
        pass
    
    @abstractmethod
    async def get_k6_version(self) -> str:
        """Get K6 version."""
        pass


class PDFGeneratorServiceInterface(ABC):
    """Interface for PDF generation service."""
    
    @abstractmethod
    async def create_pdf_report(
        self, 
        content: Dict, 
        output_path: str,
        template: Optional[str] = None
    ) -> str:
        """Create PDF report from content."""
        pass
    
    @abstractmethod
    async def generate_charts(self, data: Dict) -> List[str]:
        """Generate chart images for PDF."""
        pass
    
    @abstractmethod
    async def validate_pdf(self, pdf_path: str) -> bool:
        """Validate generated PDF file."""
        pass