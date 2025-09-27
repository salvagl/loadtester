"""
PDF Generator and Report Services
Implementation for PDF generation and technical reporting
"""

import io
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from matplotlib.backends.backend_pdf import PdfPages
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, 
    PageBreak, Image
)

from app.domain.entities.test_scenario import TestResult
from app.domain.interfaces.ai_services import (
    AIClientInterface, PDFGeneratorServiceInterface, ReportGeneratorServiceInterface
)
from app.shared.exceptions.infrastructure import ExternalServiceError

logger = logging.getLogger(__name__)

# Set matplotlib backend for headless operation
plt.switch_backend('Agg')
sns.set_style("whitegrid")


class PDFGeneratorService(PDFGeneratorServiceInterface):
    """PDF generation service using ReportLab."""
    
    def __init__(self, output_path: str):
        self.output_path = Path(output_path)
        self.output_path.mkdir(parents=True, exist_ok=True)
        
    async def create_pdf_report(
        self, 
        content: Dict, 
        output_filename: str,
        template: str = None
    ) -> str:
        """Create PDF report from content."""
        try:
            output_file = self.output_path / output_filename
            
            # Create PDF document
            doc = SimpleDocTemplate(
                str(output_file),
                pagesize=A4,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=18
            )
            
            # Build story (content)
            story = []
            styles = getSampleStyleSheet()
            
            # Add title
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                spaceAfter=30,
                textColor=colors.HexColor('#1f77b4')
            )
            
            story.append(Paragraph(content.get('title', 'LoadTester Report'), title_style))
            story.append(Spacer(1, 12))
            
            # Add executive summary
            if 'executive_summary' in content:
                story.append(Paragraph("Executive Summary", styles['Heading2']))
                story.append(Paragraph(content['executive_summary'], styles['Normal']))
                story.append(Spacer(1, 12))
            
            # Add test configuration
            if 'test_configuration' in content:
                story.append(Paragraph("Test Configuration", styles['Heading2']))
                config_data = content['test_configuration']
                
                config_table_data = [
                    ['Parameter', 'Value'],
                    ['Total Scenarios', str(config_data.get('total_scenarios', 'N/A'))],
                    ['Test Duration', f"{config_data.get('test_duration', 'N/A')} seconds"],
                    ['API Endpoints', str(config_data.get('total_endpoints', 'N/A'))],
                    ['Created At', config_data.get('created_at', 'N/A')],
                ]
                
                config_table = Table(config_table_data)
                config_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 14),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                
                story.append(config_table)
                story.append(Spacer(1, 12))
            
            # Add charts
            if 'charts' in content:
                story.append(Paragraph("Performance Analysis", styles['Heading2']))
                for chart_path in content['charts']:
                    if os.path.exists(chart_path):
                        img = Image(chart_path, width=6*inch, height=4*inch)
                        story.append(img)
                        story.append(Spacer(1, 12))
            
            # Add detailed results
            if 'detailed_results' in content:
                story.append(PageBreak())
                story.append(Paragraph("Detailed Results", styles['Heading2']))
                
                for result in content['detailed_results']:
                    story.append(Paragraph(f"Scenario: {result.get('name', 'Unknown')}", styles['Heading3']))
                    
                    result_data = [
                        ['Metric', 'Value'],
                        ['Average Response Time', f"{result.get('avg_response_time', 'N/A')} ms"],
                        ['95th Percentile', f"{result.get('p95_response_time', 'N/A')} ms"],
                        ['Total Requests', str(result.get('total_requests', 'N/A'))],
                        ['Success Rate', f"{result.get('success_rate', 'N/A')}%"],
                        ['Requests per Second', f"{result.get('rps', 'N/A')}"],
                    ]
                    
                    result_table = Table(result_data)
                    result_table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, 0), 12),
                        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                        ('GRID', (0, 0), (-1, -1), 1, colors.black)
                    ]))
                    
                    story.append(result_table)
                    story.append(Spacer(1, 12))
            
            # Add recommendations
            if 'recommendations' in content:
                story.append(Paragraph("Recommendations", styles['Heading2']))
                for i, recommendation in enumerate(content['recommendations'], 1):
                    story.append(Paragraph(f"{i}. {recommendation}", styles['Normal']))
                story.append(Spacer(1, 12))
            
            # Build PDF
            doc.build(story)
            
            logger.info(f"PDF report generated: {output_file}")
            return str(output_file)
            
        except Exception as e:
            logger.error(f"Error creating PDF report: {str(e)}")
            raise ExternalServiceError(f"PDF generation failed: {str(e)}")
    
    async def generate_charts(self, data: Dict) -> List[str]:
        """Generate chart images for PDF."""
        try:
            chart_paths = []
            
            # Response time chart
            if 'response_times' in data:
                response_time_chart = await self._create_response_time_chart(
                    data['response_times']
                )
                chart_paths.append(response_time_chart)
            
            # Throughput chart
            if 'throughput' in data:
                throughput_chart = await self._create_throughput_chart(
                    data['throughput']
                )
                chart_paths.append(throughput_chart)
            
            # Error rate chart
            if 'error_rates' in data:
                error_rate_chart = await self._create_error_rate_chart(
                    data['error_rates']
                )
                chart_paths.append(error_rate_chart)
            
            return chart_paths
            
        except Exception as e:
            logger.error(f"Error generating charts: {str(e)}")
            return []
    
    async def _create_response_time_chart(self, response_time_data: List[Dict]) -> str:
        """Create response time chart."""
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Extract data
        scenarios = [item['scenario'] for item in response_time_data]
        avg_times = [item['avg_response_time'] for item in response_time_data]
        p95_times = [item['p95_response_time'] for item in response_time_data]
        
        x = range(len(scenarios))
        
        ax.plot(x, avg_times, marker='o', label='Average Response Time', linewidth=2)
        ax.plot(x, p95_times, marker='s', label='95th Percentile', linewidth=2)
        
        ax.set_xlabel('Test Scenarios')
        ax.set_ylabel('Response Time (ms)')
        ax.set_title('Response Time Performance')
        ax.set_xticks(x)
        ax.set_xticklabels([f'Scenario {i+1}' for i in x], rotation=45)
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        chart_path = self.output_path / f"response_time_chart_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        plt.savefig(chart_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        return str(chart_path)
    
    async def _create_throughput_chart(self, throughput_data: List[Dict]) -> str:
        """Create throughput chart."""
        fig, ax = plt.subplots(figsize=(10, 6))
        
        scenarios = [item['scenario'] for item in throughput_data]
        rps = [item['requests_per_second'] for item in throughput_data]
        
        bars = ax.bar(range(len(scenarios)), rps, color='skyblue', alpha=0.7)
        
        ax.set_xlabel('Test Scenarios')
        ax.set_ylabel('Requests per Second')
        ax.set_title('Throughput Performance')
        ax.set_xticks(range(len(scenarios)))
        ax.set_xticklabels([f'Scenario {i+1}' for i in range(len(scenarios))], rotation=45)
        
        # Add value labels on bars
        for bar, value in zip(bars, rps):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{value:.1f}', ha='center', va='bottom')
        
        plt.tight_layout()
        
        chart_path = self.output_path / f"throughput_chart_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        plt.savefig(chart_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        return str(chart_path)
    
    async def _create_error_rate_chart(self, error_rate_data: List[Dict]) -> str:
        """Create error rate chart."""
        fig, ax = plt.subplots(figsize=(10, 6))
        
        scenarios = [item['scenario'] for item in error_rate_data]
        error_rates = [item['error_rate'] for item in error_rate_data]
        
        colors_list = ['green' if rate < 5 else 'orange' if rate < 10 else 'red' for rate in error_rates]
        
        bars = ax.bar(range(len(scenarios)), error_rates, color=colors_list, alpha=0.7)
        
        ax.set_xlabel('Test Scenarios')
        ax.set_ylabel('Error Rate (%)')
        ax.set_title('Error Rate Analysis')
        ax.set_xticks(range(len(scenarios)))
        ax.set_xticklabels([f'Scenario {i+1}' for i in range(len(scenarios))], rotation=45)
        ax.set_ylim(0, max(error_rates) * 1.1 if error_rates else 100)
        
        # Add horizontal line at 5% (acceptable threshold)
        ax.axhline(y=5, color='orange', linestyle='--', alpha=0.7, label='5% Threshold')
        ax.axhline(y=10, color='red', linestyle='--', alpha=0.7, label='10% Critical')
        
        # Add value labels on bars
        for bar, value in zip(bars, error_rates):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{value:.1f}%', ha='center', va='bottom')
        
        ax.legend()
        plt.tight_layout()
        
        chart_path = self.output_path / f"error_rate_chart_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        plt.savefig(chart_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        return str(chart_path)
    
    async def validate_pdf(self, pdf_path: str) -> bool:
        """Validate generated PDF file."""
        try:
            pdf_file = Path(pdf_path)
            return pdf_file.exists() and pdf_file.stat().st_size > 0
        except Exception:
            return False


class ReportGeneratorService(ReportGeneratorServiceInterface):
    """Report generation service using AI and PDF generator."""
    
    def __init__(self, ai_client: AIClientInterface, pdf_generator: PDFGeneratorService):
        self.ai_client = ai_client
        self.pdf_generator = pdf_generator
    
    async def generate_technical_report(
        self, 
        test_results: List[TestResult], 
        job_info: Dict
    ) -> str:
        """Generate technical PDF report."""
        try:
            logger.info(f"Generating technical report for {len(test_results)} test results")
            
            # Analyze results
            analysis = await self.analyze_performance_trends(test_results)
            degradation_points = await self.detect_degradation_points(test_results)
            executive_summary = await self.generate_executive_summary(test_results, job_info)
            
            # Prepare chart data
            chart_data = self._prepare_chart_data(test_results)
            
            # Generate charts
            chart_paths = await self.pdf_generator.generate_charts(chart_data)
            
            # Prepare PDF content
            content = {
                'title': f"LoadTester Performance Report",
                'executive_summary': executive_summary.get('summary', ''),
                'test_configuration': {
                    'total_scenarios': len(test_results),
                    'total_endpoints': job_info.get('total_scenarios', 0),
                    'created_at': job_info.get('created_at', '').strftime('%Y-%m-%d %H:%M:%S') if job_info.get('created_at') else 'N/A',
                    'test_duration': analysis.get('total_duration', 'N/A'),
                },
                'charts': chart_paths,
                'detailed_results': self._format_detailed_results(test_results),
                'recommendations': degradation_points,
            }
            
            # Generate PDF
            job_id = job_info.get('job_id', 'unknown')
            filename = f"loadtest_report_{job_id}.pdf"
            
            pdf_path = await self.pdf_generator.create_pdf_report(content, filename)
            
            logger.info(f"Technical report generated: {pdf_path}")
            return pdf_path
            
        except Exception as e:
            logger.error(f"Error generating technical report: {str(e)}")
            raise ExternalServiceError(f"Report generation failed: {str(e)}")
    
    async def generate_executive_summary(
        self, 
        test_results: List[TestResult], 
        job_info: Dict
    ) -> Dict:
        """Generate executive summary for report."""
        try:
            # Prepare summary data
            total_requests = sum(r.total_requests or 0 for r in test_results)
            total_errors = sum(r.failed_requests or 0 for r in test_results)
            avg_response_time = sum(r.avg_response_time_ms or 0 for r in test_results) / len(test_results) if test_results else 0
            
            prompt = f"""
            Create an executive summary for a load testing report with the following data:
            
            Test Results Summary:
            - Total Test Scenarios: {len(test_results)}
            - Total Requests: {total_requests}
            - Total Errors: {total_errors}
            - Average Response Time: {avg_response_time:.2f} ms
            - Error Rate: {(total_errors / total_requests * 100) if total_requests > 0 else 0:.2f}%
            
            Write a professional executive summary (2-3 paragraphs) that:
            1. Summarizes the test execution
            2. Highlights key performance findings
            3. Mentions any degradation points found
            4. Provides high-level recommendations
            
            Keep it business-focused and non-technical.
            """
            
            messages = [{"role": "user", "content": prompt}]
            summary = await self.ai_client.chat_completion(messages, max_tokens=500)
            
            return {
                'summary': summary.strip(),
                'key_metrics': {
                    'total_scenarios': len(test_results),
                    'total_requests': total_requests,
                    'error_rate': (total_errors / total_requests * 100) if total_requests > 0 else 0,
                    'avg_response_time': avg_response_time,
                }
            }
            
        except Exception as e:
            logger.error(f"Error generating executive summary: {str(e)}")
            return {
                'summary': "Executive summary could not be generated due to technical issues.",
                'key_metrics': {}
            }
    
    async def analyze_performance_trends(self, test_results: List[TestResult]) -> Dict:
        """Analyze performance trends across test results."""
        if not test_results:
            return {}
        
        trends = {
            'response_time_trend': 'stable',
            'throughput_trend': 'stable',
            'error_rate_trend': 'stable',
            'degradation_detected': False,
            'total_duration': sum(getattr(r.execution, 'actual_duration_seconds', 0) for r in test_results if hasattr(r, 'execution')),
        }
        
        # Analyze response time trend
        response_times = [r.avg_response_time_ms for r in test_results if r.avg_response_time_ms]
        if len(response_times) > 1:
            if response_times[-1] > response_times[0] * 1.5:
                trends['response_time_trend'] = 'degrading'
            elif response_times[-1] < response_times[0] * 0.8:
                trends['response_time_trend'] = 'improving'
        
        # Analyze error rate trend
        error_rates = [r.error_rate_percent for r in test_results]
        if any(rate > 50 for rate in error_rates):
            trends['degradation_detected'] = True
            trends['error_rate_trend'] = 'critical'
        
        return trends
    
    async def detect_degradation_points(self, test_results: List[TestResult]) -> List[str]:
        """Detect degradation points in test results."""
        recommendations = []
        
        if not test_results:
            return recommendations
        
        # Check for high error rates
        high_error_results = [r for r in test_results if r.error_rate_percent > 10]
        if high_error_results:
            recommendations.append(
                f"High error rate detected in {len(high_error_results)} scenarios. "
                "Consider optimizing server capacity or reviewing application code."
            )
        
        # Check for response time degradation
        response_times = [r.avg_response_time_ms for r in test_results if r.avg_response_time_ms]
        if len(response_times) > 1:
            baseline = response_times[0]
            degraded_scenarios = [i for i, rt in enumerate(response_times) if rt > baseline * 3]
            
            if degraded_scenarios:
                recommendations.append(
                    f"Response time degradation detected starting at scenario {degraded_scenarios[0] + 1}. "
                    "This indicates the system reached its performance limits."
                )
        
        # Check for throughput issues
        throughputs = [r.requests_per_second for r in test_results if r.requests_per_second]
        if throughputs and any(t < max(throughputs) * 0.5 for t in throughputs[-3:]):
            recommendations.append(
                "Throughput degradation observed in final scenarios. "
                "Consider implementing load balancing or scaling strategies."
            )
        
        if not recommendations:
            recommendations.append(
                "No significant performance degradation detected. "
                "The system performed within acceptable parameters for the tested load."
            )
        
        return recommendations
    
    def _prepare_chart_data(self, test_results: List[TestResult]) -> Dict:
        """Prepare data for chart generation."""
        chart_data = {
            'response_times': [],
            'throughput': [],
            'error_rates': [],
        }
        
        for i, result in enumerate(test_results):
            chart_data['response_times'].append({
                'scenario': f'Scenario {i+1}',
                'avg_response_time': result.avg_response_time_ms or 0,
                'p95_response_time': result.p95_response_time_ms or 0,
            })
            
            chart_data['throughput'].append({
                'scenario': f'Scenario {i+1}',
                'requests_per_second': result.requests_per_second or 0,
            })
            
            chart_data['error_rates'].append({
                'scenario': f'Scenario {i+1}',
                'error_rate': result.error_rate_percent,
            })
        
        return chart_data
    
    def _format_detailed_results(self, test_results: List[TestResult]) -> List[Dict]:
        """Format detailed results for PDF table."""
        detailed_results = []
        
        for i, result in enumerate(test_results):
            detailed_results.append({
                'name': f'Scenario {i+1}',
                'avg_response_time': f"{result.avg_response_time_ms or 0:.2f}",
                'p95_response_time': f"{result.p95_response_time_ms or 0:.2f}",
                'total_requests': result.total_requests or 0,
                'success_rate': f"{result.success_rate_percent or 0:.2f}",
                'rps': f"{result.requests_per_second or 0:.2f}",
            })
        
        return detailed_results