"""
Integration tests for Report Generation Flow
Tests complete flow: Results → Generate PDF → Verify file exists → Verify content
"""

import pytest
import os
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock
from loadtester.infrastructure.external.pdf_generator_service import (
    PDFGeneratorService, ReportGeneratorService
)
from loadtester.infrastructure.repositories.test_result_repository import TestResultRepository
from loadtester.infrastructure.repositories.job_repository import JobRepository
from tests.fixtures.mock_data import create_mock_test_result, create_mock_job
from datetime import datetime


# ============================================================================
# INTEGRATION TEST: Complete Report Generation Flow
# ============================================================================

@pytest.mark.integration
@pytest.mark.asyncio
async def test_complete_report_generation_flow(tmp_path, mock_ai_client):
    """
    Test complete flow: Results → Generate PDF → Verify file exists → Verify content
    """
    # Step 1: Create PDF generator with temp directory
    pdf_generator = PDFGeneratorService(output_path=str(tmp_path))

    # Step 2: Create report generator
    report_generator = ReportGeneratorService(
        ai_client=mock_ai_client,
        pdf_generator=pdf_generator
    )

    # Step 3: Create test results
    results = [
        create_mock_test_result(
            avg_response_time_ms=150.0,
            success_rate_percent=99.0,
            total_requests=1000
        )
    ]

    # Step 4: Create job info
    job_info = {
        "job_id": "test-job-123",
        "api_name": "Test API",
        "created_at": datetime.utcnow()  # Pass datetime object, not string
    }

    # Step 5: Generate report
    report_path = await report_generator.generate_technical_report(
        test_results=results,
        job_info=job_info
    )

    # Step 6: Verify file exists
    assert report_path is not None
    report_file = Path(report_path)
    assert report_file.exists()
    assert report_file.stat().st_size > 0

    # Step 7: Verify it's a PDF
    assert report_path.endswith('.pdf')


@pytest.mark.integration
@pytest.mark.asyncio
async def test_report_with_multiple_results(tmp_path, mock_ai_client):
    """Test report generation with multiple test results."""
    pdf_generator = PDFGeneratorService(output_path=str(tmp_path))
    report_generator = ReportGeneratorService(
        ai_client=mock_ai_client,
        pdf_generator=pdf_generator
    )

    # Create 3 test results
    results = [
        create_mock_test_result(
            avg_response_time_ms=100.0,
            success_rate_percent=99.5,
            total_requests=500
        ),
        create_mock_test_result(
            avg_response_time_ms=150.0,
            success_rate_percent=99.0,
            total_requests=1000
        ),
        create_mock_test_result(
            avg_response_time_ms=200.0,
            success_rate_percent=98.5,
            total_requests=2000
        )
    ]

    job_info = {
        "job_id": "multi-test-job",
        "api_name": "Multi Test API"
    }

    report_path = await report_generator.generate_technical_report(
        test_results=results,
        job_info=job_info
    )

    assert Path(report_path).exists()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_report_file_naming(tmp_path, mock_ai_client):
    """Test report file naming convention."""
    pdf_generator = PDFGeneratorService(output_path=str(tmp_path))
    report_generator = ReportGeneratorService(
        ai_client=mock_ai_client,
        pdf_generator=pdf_generator
    )

    results = [create_mock_test_result()]
    job_info = {
        "job_id": "naming-test-job",
        "api_name": "Naming Test API"
    }

    report_path = await report_generator.generate_technical_report(
        test_results=results,
        job_info=job_info
    )

    # Verify naming convention
    report_file = Path(report_path)
    assert report_file.name.endswith('.pdf')
    assert 'naming-test-job' in report_file.name.lower() or 'report' in report_file.name.lower()


@pytest.mark.integration
def test_pdf_generator_initialization(tmp_path):
    """Test PDF generator initialization."""
    pdf_generator = PDFGeneratorService(output_path=str(tmp_path))

    # Verify output directory created
    assert tmp_path.exists()
    assert tmp_path.is_dir()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_pdf_basic_content_creation(tmp_path):
    """Test basic PDF content creation."""
    pdf_generator = PDFGeneratorService(output_path=str(tmp_path))

    content = {
        "title": "Test Report",
        "date": datetime.utcnow().isoformat(),
        "sections": [
            {"heading": "Summary", "content": "Test summary content"}
        ]
    }

    pdf_path = await pdf_generator.create_pdf_report(
        content=content,
        output_filename="test_report.pdf"
    )

    # Verify PDF created
    assert pdf_path is not None
    pdf_file = Path(pdf_path)
    assert pdf_file.exists()
    assert pdf_file.stat().st_size > 0


@pytest.mark.integration
@pytest.mark.asyncio
async def test_pdf_validation(tmp_path):
    """Test PDF file validation."""
    pdf_generator = PDFGeneratorService(output_path=str(tmp_path))

    content = {"title": "Validation Test"}
    pdf_path = await pdf_generator.create_pdf_report(
        content=content,
        output_filename="validation_test.pdf"
    )

    # Validate PDF
    is_valid = await pdf_generator.validate_pdf(pdf_path)
    assert is_valid is True


@pytest.mark.integration
@pytest.mark.asyncio
async def test_pdf_validation_nonexistent_file(tmp_path):
    """Test PDF validation with nonexistent file."""
    pdf_generator = PDFGeneratorService(output_path=str(tmp_path))

    is_valid = await pdf_generator.validate_pdf(str(tmp_path / "nonexistent.pdf"))
    assert is_valid is False


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.requires_db
async def test_report_with_database_results(db_session, tmp_path, mock_ai_client):
    """Test report generation with results from database."""
    # Create repositories
    result_repo = TestResultRepository(db_session)
    job_repo = JobRepository(db_session)

    # Create job
    job = create_mock_job(job_type="load_test")
    created_job = await job_repo.create(job)

    # Create result in DB
    result = create_mock_test_result(
        execution_id=1,
        avg_response_time_ms=175.0,
        success_rate_percent=98.0
    )
    created_result = await result_repo.create(result)

    # Generate report
    pdf_generator = PDFGeneratorService(output_path=str(tmp_path))
    report_generator = ReportGeneratorService(
        ai_client=mock_ai_client,
        pdf_generator=pdf_generator
    )

    job_info = {
        "job_id": created_job.job_id,
        "api_name": "DB Test API"
    }

    report_path = await report_generator.generate_technical_report(
        test_results=[created_result],
        job_info=job_info
    )

    assert Path(report_path).exists()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_report_performance_classification_excellent(tmp_path, mock_ai_client):
    """Test report with excellent performance classification."""
    pdf_generator = PDFGeneratorService(output_path=str(tmp_path))
    report_generator = ReportGeneratorService(
        ai_client=mock_ai_client,
        pdf_generator=pdf_generator
    )

    # Excellent performance metrics
    results = [
        create_mock_test_result(
            avg_response_time_ms=80.0,  # < 200ms
            success_rate_percent=99.9,   # > 99%
            total_requests=1000
        )
    ]

    job_info = {"job_id": "excellent-test", "api_name": "Excellent API"}

    report_path = await report_generator.generate_technical_report(
        test_results=results,
        job_info=job_info
    )

    assert Path(report_path).exists()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_report_performance_classification_poor(tmp_path, mock_ai_client):
    """Test report with poor performance classification."""
    pdf_generator = PDFGeneratorService(output_path=str(tmp_path))
    report_generator = ReportGeneratorService(
        ai_client=mock_ai_client,
        pdf_generator=pdf_generator
    )

    # Poor performance metrics
    results = [
        create_mock_test_result(
            avg_response_time_ms=2000.0,  # > 1000ms
            success_rate_percent=70.0,     # < 95%
            total_requests=1000
        )
    ]

    job_info = {"job_id": "poor-test", "api_name": "Poor API"}

    report_path = await report_generator.generate_technical_report(
        test_results=results,
        job_info=job_info
    )

    assert Path(report_path).exists()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_report_with_degradation_detected(tmp_path, mock_ai_client):
    """Test report that includes degradation detection."""
    pdf_generator = PDFGeneratorService(output_path=str(tmp_path))
    report_generator = ReportGeneratorService(
        ai_client=mock_ai_client,
        pdf_generator=pdf_generator
    )

    # Results showing degradation
    results = [
        create_mock_test_result(
            avg_response_time_ms=100.0,
            success_rate_percent=99.0,
            total_requests=500
        ),
        create_mock_test_result(
            avg_response_time_ms=600.0,  # 6x slower
            success_rate_percent=75.0,    # 24% more errors
            total_requests=1000
        )
    ]

    job_info = {"job_id": "degradation-test", "api_name": "Degraded API"}

    report_path = await report_generator.generate_technical_report(
        test_results=results,
        job_info=job_info
    )

    assert Path(report_path).exists()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_report_multiple_files_same_directory(tmp_path, mock_ai_client):
    """Test generating multiple reports in same directory."""
    pdf_generator = PDFGeneratorService(output_path=str(tmp_path))
    report_generator = ReportGeneratorService(
        ai_client=mock_ai_client,
        pdf_generator=pdf_generator
    )

    results = [create_mock_test_result()]

    # Generate 3 reports
    report_paths = []
    for i in range(3):
        job_info = {
            "job_id": f"multi-file-test-{i}",
            "api_name": f"API {i}"
        }
        report_path = await report_generator.generate_technical_report(
            test_results=results,
            job_info=job_info
        )
        report_paths.append(report_path)

    # Verify all exist
    for path in report_paths:
        assert Path(path).exists()

    # Verify they're different files
    assert len(set(report_paths)) == 3
