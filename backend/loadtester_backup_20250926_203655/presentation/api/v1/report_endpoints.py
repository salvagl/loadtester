"""
Report API Endpoints
FastAPI endpoints for report download and management
"""

import logging
import os
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse

from app.domain.services.load_test_service import LoadTestService
from app.infrastructure.config.dependencies import get_load_test_service
from app.settings import get_settings

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/report/{job_id}",
    summary="Download Report",
    description="Download the PDF report for a completed load test job",
    response_class=FileResponse
)
async def download_report(
    job_id: str,
    load_test_service: LoadTestService = Depends(get_load_test_service)
) -> FileResponse:
    """Download PDF report for a completed job."""
    try:
        logger.info(f"Download request for report: {job_id}")
        
        # Get job status to verify it's finished
        status_data = await load_test_service.get_job_status(job_id)
        
        if status_data["status"] != "FINISHED":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Report not available. Job status: {status_data['status']}"
            )
        
        # Get report path from job result data
        if "report_url" not in status_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Report not found for this job"
            )
        
        # Construct file path
        settings = get_settings()
        report_filename = f"loadtest_report_{job_id}.pdf"
        report_path = Path(settings.reports_path) / report_filename
        
        if not report_path.exists():
            logger.error(f"Report file not found: {report_path}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Report file not found"
            )
        
        logger.info(f"Serving report file: {report_path}")
        
        return FileResponse(
            path=str(report_path),
            filename=report_filename,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={report_filename}",
                "Cache-Control": "no-cache",
            }
        )
        
    except HTTPException:
        raise
    
    except Exception as e:
        logger.error(f"Error downloading report {job_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving report"
        )


@router.get(
    "/reports",
    summary="List Available Reports",
    description="Get list of available reports"
)
async def list_reports(
    load_test_service: LoadTestService = Depends(get_load_test_service)
) -> dict:
    """List all available reports."""
    try:
        settings = get_settings()
        reports_dir = Path(settings.reports_path)
        
        if not reports_dir.exists():
            return {"reports": []}
        
        reports = []
        for pdf_file in reports_dir.glob("*.pdf"):
            # Extract job_id from filename
            if pdf_file.name.startswith("loadtest_report_"):
                job_id = pdf_file.name.replace("loadtest_report_", "").replace(".pdf", "")
                
                reports.append({
                    "job_id": job_id,
                    "filename": pdf_file.name,
                    "size": pdf_file.stat().st_size,
                    "created_at": pdf_file.stat().st_mtime,
                    "download_url": f"/api/v1/report/{job_id}"
                })
        
        # Sort by creation time (newest first)
        reports.sort(key=lambda x: x["created_at"], reverse=True)
        
        return {
            "reports": reports,
            "total": len(reports)
        }
        
    except Exception as e:
        logger.error(f"Error listing reports: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving reports list"
        )


@router.delete(
    "/report/{job_id}",
    summary="Delete Report",
    description="Delete a report file"
)
async def delete_report(
    job_id: str,
    load_test_service: LoadTestService = Depends(get_load_test_service)
) -> dict:
    """Delete a report file."""
    try:
        settings = get_settings()
        report_filename = f"loadtest_report_{job_id}.pdf"
        report_path = Path(settings.reports_path) / report_filename
        
        if not report_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Report not found"
            )
        
        # Delete the file
        report_path.unlink()
        
        logger.info(f"Deleted report: {report_filename}")
        
        return {
            "message": f"Report {job_id} deleted successfully",
            "job_id": job_id
        }
        
    except HTTPException:
        raise
    
    except Exception as e:
        logger.error(f"Error deleting report {job_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error deleting report"
        )


@router.get(
    "/report/{job_id}/info",
    summary="Get Report Info",
    description="Get information about a report without downloading it"
)
async def get_report_info(
    job_id: str,
    load_test_service: LoadTestService = Depends(get_load_test_service)
) -> dict:
    """Get information about a report."""
    try:
        # Get job status
        status_data = await load_test_service.get_job_status(job_id)
        
        if status_data["status"] != "FINISHED":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Report not available. Job status: {status_data['status']}"
            )
        
        # Check if report file exists
        settings = get_settings()
        report_filename = f"loadtest_report_{job_id}.pdf"
        report_path = Path(settings.reports_path) / report_filename
        
        if not report_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Report file not found"
            )
        
        file_stats = report_path.stat()
        
        return {
            "job_id": job_id,
            "filename": report_filename,
            "size": file_stats.st_size,
            "created_at": file_stats.st_mtime,
            "job_status": status_data["status"],
            "job_created_at": status_data.get("created_at"),
            "job_finished_at": status_data.get("finished_at"),
            "download_url": f"/api/v1/report/{job_id}"
        }
        
    except HTTPException:
        raise
    
    except Exception as e:
        logger.error(f"Error getting report info {job_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving report information"
        )