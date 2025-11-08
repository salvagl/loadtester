"""
Unit tests for PDF Generator Service
Tests helper functions and data preparation for PDF generation
"""

import pytest
from pathlib import Path
import tempfile
from unittest.mock import MagicMock, AsyncMock
from loadtester.infrastructure.external.pdf_generator_service import (
    PDFGeneratorService,
    ReportGeneratorService
)
from tests.fixtures.mock_data import create_mock_test_result, create_mock_degraded_result


# ============================================================================
# TEST FIXTURES
# ============================================================================

@pytest.fixture
def temp_output_dir():
    """Create temporary directory for PDF output."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def pdf_generator(temp_output_dir):
    """Create PDFGeneratorService instance."""
    return PDFGeneratorService(output_path=temp_output_dir)


@pytest.fixture
def mock_ai_client():
    """Mock AI client."""
    client = MagicMock()
    client.chat_completion = AsyncMock(return_value="Test recommendation")
    return client


@pytest.fixture
def report_generator(mock_ai_client, pdf_generator):
    """Create ReportGeneratorService instance."""
    return ReportGeneratorService(
        ai_client=mock_ai_client,
        pdf_generator=pdf_generator
    )


# ============================================================================
# PDF GENERATOR INITIALIZATION TESTS
# ============================================================================

@pytest.mark.unit
def test_pdf_generator_creates_output_directory(temp_output_dir):
    """Test that PDF generator creates output directory."""
    output_path = Path(temp_output_dir) / "reports"
    generator = PDFGeneratorService(output_path=str(output_path))

    assert output_path.exists()
    assert output_path.is_dir()


@pytest.mark.unit
def test_pdf_generator_stores_output_path(pdf_generator, temp_output_dir):
    """Test that PDF generator stores output path."""
    assert pdf_generator.output_path == Path(temp_output_dir)


# ============================================================================
# PERFORMANCE CLASSIFICATION TESTS
# ============================================================================

@pytest.mark.unit
def test_classify_performance_excellent(report_generator):
    """Test classification of excellent performance."""
    result = create_mock_test_result(
        avg_response_time_ms=150.0,
        success_rate_percent=99.0
    )

    classification = report_generator._classify_performance(result)

    assert classification == 'Excelente'


@pytest.mark.unit
def test_classify_performance_good(report_generator):
    """Test classification of good performance."""
    result = create_mock_test_result(
        avg_response_time_ms=350.0,
        success_rate_percent=99.0
    )

    classification = report_generator._classify_performance(result)

    assert classification == 'Bueno'


@pytest.mark.unit
def test_classify_performance_degraded_by_time(report_generator):
    """Test classification of degraded performance by response time."""
    result = create_mock_test_result(
        avg_response_time_ms=750.0,
        success_rate_percent=99.0
    )

    classification = report_generator._classify_performance(result)

    assert classification == 'Degradado'


@pytest.mark.unit
def test_classify_performance_degraded_by_error_rate(report_generator):
    """Test classification of degraded performance by error rate."""
    result = create_mock_test_result(
        avg_response_time_ms=100.0,
        success_rate_percent=85.0  # 15% error rate
    )

    classification = report_generator._classify_performance(result)

    assert classification == 'Degradado'


@pytest.mark.unit
def test_classify_performance_critical_by_time(report_generator):
    """Test classification of critical performance by response time."""
    result = create_mock_test_result(
        avg_response_time_ms=1500.0,
        success_rate_percent=99.0
    )

    classification = report_generator._classify_performance(result)

    assert classification == 'Crítico'


@pytest.mark.unit
def test_classify_performance_critical_by_error_rate(report_generator):
    """Test classification of critical performance by error rate."""
    result = create_mock_degraded_result()  # 55% error rate

    classification = report_generator._classify_performance(result)

    assert classification == 'Crítico'


@pytest.mark.unit
def test_classify_performance_unknown(report_generator):
    """Test classification when response time is None."""
    result = create_mock_test_result(
        avg_response_time_ms=None,
        success_rate_percent=99.0
    )

    classification = report_generator._classify_performance(result)

    assert classification == 'Desconocido'


# ============================================================================
# RECOMMENDATIONS GENERATION TESTS
# ============================================================================

@pytest.mark.unit
@pytest.mark.asyncio
async def test_generate_recommendations_no_results(report_generator):
    """Test recommendations with no results."""
    recommendations = await report_generator._generate_performance_recommendations([])

    assert len(recommendations) > 0
    assert any("No hay resultados" in rec for rec in recommendations)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_generate_recommendations_high_response_time(report_generator):
    """Test recommendations for high response time."""
    results = [
        create_mock_test_result(avg_response_time_ms=1200.0, success_rate_percent=99.0)
    ]

    recommendations = await report_generator._generate_performance_recommendations(results)

    assert len(recommendations) > 0
    assert any("Crítico" in rec or "1000ms" in rec for rec in recommendations)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_generate_recommendations_moderate_response_time(report_generator):
    """Test recommendations for moderate response time."""
    results = [
        create_mock_test_result(avg_response_time_ms=600.0, success_rate_percent=99.0)
    ]

    recommendations = await report_generator._generate_performance_recommendations(results)

    assert len(recommendations) > 0
    assert any("Advertencia" in rec or "500ms" in rec for rec in recommendations)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_generate_recommendations_low_success_rate(report_generator):
    """Test recommendations for low success rate."""
    results = [
        create_mock_test_result(avg_response_time_ms=100.0, success_rate_percent=85.0)
    ]

    recommendations = await report_generator._generate_performance_recommendations(results)

    assert len(recommendations) > 0
    assert any("Tasa de Errores" in rec or "85" in rec for rec in recommendations)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_generate_recommendations_good_performance(report_generator):
    """Test recommendations for good performance."""
    results = [
        create_mock_test_result(avg_response_time_ms=150.0, success_rate_percent=99.5)
    ]

    recommendations = await report_generator._generate_performance_recommendations(results)

    assert len(recommendations) > 0
    # Should have positive recommendations
    assert any("aceptables" in rec or "monitoreo" in rec.lower() for rec in recommendations)


# ============================================================================
# CHART DATA PREPARATION TESTS
# ============================================================================

@pytest.mark.unit
def test_prepare_chart_data_empty(report_generator):
    """Test chart data preparation with empty results."""
    chart_data = report_generator._prepare_chart_data([])

    assert isinstance(chart_data, dict)
    assert "response_times" in chart_data
    assert "throughput" in chart_data
    assert "error_rates" in chart_data


@pytest.mark.unit
def test_prepare_chart_data_with_results(report_generator):
    """Test chart data preparation with results."""
    results = [
        create_mock_test_result(
            avg_response_time_ms=150.0,
            requests_per_second=100.0,
            success_rate_percent=99.0
        ),
        create_mock_test_result(
            avg_response_time_ms=200.0,
            requests_per_second=95.0,
            success_rate_percent=98.0
        )
    ]

    chart_data = report_generator._prepare_chart_data(results)

    assert len(chart_data["response_times"]) == 2
    assert len(chart_data["throughput"]) == 2
    assert len(chart_data["error_rates"]) == 2


# ============================================================================
# DETAILED RESULTS FORMATTING TESTS
# ============================================================================

@pytest.mark.unit
def test_format_detailed_results_empty(report_generator):
    """Test formatting empty results."""
    formatted = report_generator._format_detailed_results([])

    assert isinstance(formatted, list)
    assert len(formatted) == 0


@pytest.mark.unit
def test_format_detailed_results_with_data(report_generator):
    """Test formatting results with data."""
    results = [
        create_mock_test_result(
            avg_response_time_ms=150.0,
            p95_response_time_ms=300.0,
            success_rate_percent=99.0,
            total_requests=1000
        )
    ]

    formatted = report_generator._format_detailed_results(results)

    assert isinstance(formatted, list)
    assert len(formatted) == 1
    assert isinstance(formatted[0], dict)


# ============================================================================
# ENDPOINT SUMMARY TESTS
# ============================================================================

@pytest.mark.unit
def test_generate_endpoint_summary_empty(report_generator):
    """Test generating endpoint summary with empty results."""
    summary = report_generator._generate_endpoint_summary([])

    assert isinstance(summary, dict)


@pytest.mark.unit
def test_generate_endpoint_summary_with_results(report_generator):
    """Test generating endpoint summary with results."""
    results = [
        create_mock_test_result(
            avg_response_time_ms=150.0,
            success_rate_percent=99.0,
            total_requests=1000
        ),
        create_mock_test_result(
            avg_response_time_ms=200.0,
            success_rate_percent=98.0,
            total_requests=900
        )
    ]

    summary = report_generator._generate_endpoint_summary(results)

    assert isinstance(summary, dict)
    # Summary should contain aggregated metrics


# ============================================================================
# PDF CREATION TESTS
# ============================================================================

@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_pdf_report_creates_file(pdf_generator, temp_output_dir):
    """Test that PDF report file is created."""
    content = {
        'title': 'Test Report',
        'test_configuration': {'created_at': '2025-01-01'}
    }

    result_path = await pdf_generator.create_pdf_report(
        content=content,
        output_filename='test_report.pdf'
    )

    # Check that file was created
    output_file = Path(temp_output_dir) / 'test_report.pdf'
    assert output_file.exists()
    assert result_path == str(output_file)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_pdf_report_returns_path(pdf_generator):
    """Test that PDF creation returns file path."""
    content = {
        'title': 'Test Report',
        'test_configuration': {'created_at': '2025-01-01'}
    }

    result_path = await pdf_generator.create_pdf_report(
        content=content,
        output_filename='test.pdf'
    )

    assert isinstance(result_path, str)
    assert result_path.endswith('test.pdf')


# ============================================================================
# EDGE CASES AND ERROR HANDLING TESTS
# ============================================================================

@pytest.mark.unit
def test_classify_performance_handles_none_success_rate(report_generator):
    """Test performance classification with None success rate."""
    result = create_mock_test_result(
        avg_response_time_ms=150.0,
        success_rate_percent=None
    )

    # Should not crash
    classification = report_generator._classify_performance(result)
    assert classification in ['Excelente', 'Bueno', 'Degradado', 'Crítico', 'Desconocido']


@pytest.mark.unit
@pytest.mark.asyncio
async def test_generate_recommendations_handles_none_values(report_generator):
    """Test recommendations generation with None values."""
    results = [
        create_mock_test_result(
            avg_response_time_ms=None,
            success_rate_percent=None
        )
    ]

    # Should not crash
    recommendations = await report_generator._generate_performance_recommendations(results)
    assert isinstance(recommendations, list)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_pdf_with_minimal_content(pdf_generator):
    """Test PDF creation with minimal content."""
    content = {'title': 'Minimal Report'}

    result_path = await pdf_generator.create_pdf_report(
        content=content,
        output_filename='minimal.pdf'
    )

    assert Path(result_path).exists()


@pytest.mark.unit
def test_prepare_chart_data_handles_none_values(report_generator):
    """Test chart data preparation with None values in results."""
    results = [
        create_mock_test_result(
            avg_response_time_ms=None,
            requests_per_second=None,
            success_rate_percent=None
        )
    ]

    # Should not crash
    chart_data = report_generator._prepare_chart_data(results)
    assert isinstance(chart_data, dict)
