"""
Status API Endpoints
FastAPI endpoints for job status and system health
"""

import logging
from typing import Dict

from fastapi import APIRouter, Depends, HTTPException, status

from loadtester.domain.services.load_test_service import LoadTestService
from loadtester.infrastructure.config.dependencies import get_load_test_service
from loadtester.settings import get_settings

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/status/{job_id}",
    summary="Get Job Status",
    description="Get the current status and progress of a load test job"
)
async def get_job_status(
    job_id: str,
    load_test_service: LoadTestService = Depends(get_load_test_service)
) -> Dict:
    """Get job status and progress."""
    try:
        logger.debug(f"Getting status for job: {job_id}")
        
        status_data = await load_test_service.get_job_status(job_id)
        
        return status_data
        
    except Exception as e:
        logger.error(f"Error getting job status {job_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found"
        )


@router.get(
    "/health",
    summary="Health Check",
    description="Check the health status of the LoadTester service"
)
async def health_check() -> Dict:
    """Health check endpoint."""
    settings = get_settings()
    
    health_status = {
        "status": "healthy",
        "service": settings.app_name,
        "version": settings.app_version,
        "timestamp": "2024-01-01T00:00:00Z",  # Would use actual timestamp
    }
    
    return health_status


@router.get(
    "/system/info",
    summary="System Information",
    description="Get system information and configuration"
)
async def get_system_info() -> Dict:
    """Get system information."""
    settings = get_settings()
    
    return {
        "service": {
            "name": settings.app_name,
            "version": settings.app_version,
            "debug": settings.debug,
        },
        "configuration": {
            "max_concurrent_jobs": settings.max_concurrent_jobs,
            "max_file_size": settings.max_file_size,
            "default_test_duration": settings.default_test_duration,
            "degradation_settings": {
                "response_time_multiplier": settings.degradation_response_time_multiplier,
                "error_rate_threshold": settings.degradation_error_rate_threshold,
                "initial_user_percentage": settings.initial_user_percentage,
                "user_increment_percentage": settings.user_increment_percentage,
                "stop_error_threshold": settings.stop_error_threshold,
            }
        },
        "features": {
            "ai_services_available": settings.has_ai_service,
            "supported_file_types": settings.allowed_file_extensions_list,
        }
    }


@router.get(
    "/metrics",
    summary="System Metrics",
    description="Get basic system metrics"
)
async def get_metrics(
    load_test_service: LoadTestService = Depends(get_load_test_service)
) -> Dict:
    """Get system metrics."""
    try:
        # This would typically get metrics from the repositories
        # For now, return basic metrics structure
        
        return {
            "jobs": {
                "total": 0,
                "pending": 0,
                "running": 0,
                "finished": 0,
                "failed": 0,
            },
            "tests": {
                "total_executions": 0,
                "total_scenarios": 0,
                "avg_execution_time": 0,
            },
            "system": {
                "uptime": "0h 0m 0s",
                "memory_usage": "0 MB",
                "disk_usage": "0 MB",
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting metrics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving metrics"
        )