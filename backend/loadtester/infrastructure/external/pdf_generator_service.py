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

from loadtester.domain.entities.domain_entities import TestResult
from loadtester.domain.interfaces.service_interfaces import (
    AIClientInterface, PDFGeneratorServiceInterface, ReportGeneratorServiceInterface
)
from loadtester.shared.exceptions.infrastructure_exceptions import ExternalServiceError

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
                story.append(Paragraph("Resumen Ejecutivo", styles['Heading2']))
                story.append(Paragraph(content['executive_summary'], styles['Normal']))
                story.append(Spacer(1, 12))
            
            # Add test configuration
            if 'test_configuration' in content:
                story.append(Paragraph("Configuración de Prueba", styles['Heading2']))
                config_data = content['test_configuration']

                config_table_data = [
                    ['Parámetro', 'Valor'],
                    ['Total Escenarios', str(config_data.get('total_scenarios', 'N/A'))],
                    ['Duración Prueba', f"{config_data.get('test_duration', 'N/A')} segundos"],
                    ['Endpoints API', str(config_data.get('total_endpoints', 'N/A'))],
                    ['Creado el', config_data.get('created_at', 'N/A')],
                    ['Versión K6', config_data.get('k6_version', 'N/A')],
                    ['Estrategia de Prueba', config_data.get('load_testing_strategy', 'N/A')],
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
                story.append(Paragraph("Análisis de Rendimiento", styles['Heading2']))
                for chart_path in content['charts']:
                    if os.path.exists(chart_path):
                        img = Image(chart_path, width=6*inch, height=4*inch)
                        story.append(img)
                        story.append(Spacer(1, 12))
            
            # Add explanatory section for charts
            if 'charts' in content and content['charts']:
                story.append(Paragraph("Interpretación de Gráficas", styles['Heading3']))

                interpretation_text = """
                <b>Cómo interpretar las gráficas de rendimiento:</b><br/><br/>

                <b>1. Gráfica de Tiempos de Respuesta:</b> Muestra la evolución de los tiempos de respuesta a medida que aumenta la carga.
                Las líneas de umbrales (naranja y roja) indican niveles de degradación. Si las líneas de medición superan estos umbrales,
                el sistema está experimentando degradación del rendimiento.<br/><br/>

                <b>2. Gráfica de Capacidad de Procesamiento:</b> Representa cuántas peticiones por segundo puede procesar el sistema.
                Una caída en el throughput indica que el sistema está alcanzando su límite de capacidad.<br/><br/>

                <b>3. Gráfica de Tasa de Errores:</b> Muestra el porcentaje de peticiones que fallan. Los umbrales al 5% y 10%
                indican niveles aceptables y críticos respectivamente. Valores por encima del 10% requieren atención inmediata.
                """

                story.append(Paragraph(interpretation_text, styles['Normal']))
                story.append(Spacer(1, 12))

            # Degradation Analysis Section
            if 'degradation_analysis' in content:
                story.append(PageBreak())
                story.append(Paragraph("Análisis de Degradación del Rendimiento", styles['Heading2']))
                degradation_data = content['degradation_analysis']

                if degradation_data:
                    degradation_text = "Puntos de degradación detectados en los siguientes escenarios:"
                    for point in degradation_data:
                        degradation_text += f"<br/>• {point}"
                else:
                    degradation_text = "No se detectó degradación significativa del rendimiento en todos los escenarios de prueba."

                story.append(Paragraph(degradation_text, styles['Normal']))
                story.append(Spacer(1, 12))

            # Endpoint Summary Section
            if 'endpoint_summary' in content:
                story.append(Paragraph("Análisis por Endpoint", styles['Heading2']))
                endpoint_data = content['endpoint_summary']

                # Summary paragraph
                story.append(Paragraph(endpoint_data.get('summary', ''), styles['Normal']))
                story.append(Spacer(1, 12))

                # Endpoint performance table
                if endpoint_data.get('endpoints'):
                    endpoint_table_data = [
                        ['Endpoint', 'Método', 'Resp. Promedio (ms)', 'Tasa Éxito (%)', 'Clasificación', 'Degradación']
                    ]

                    for ep in endpoint_data['endpoints']:
                        degradation_status = "⚠️ SÍ" if ep['degradation_detected'] else "✓ NO"
                        endpoint_table_data.append([
                            ep['endpoint'],
                            ep['method'],
                            f"{ep['avg_response_time']:.1f}",
                            f"{ep['success_rate']:.1f}",
                            ep['performance_classification'],
                            degradation_status
                        ])

                    endpoint_table = Table(endpoint_table_data)
                    endpoint_table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.navy),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, 0), 12),
                        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                        ('BACKGROUND', (0, 1), (-1, -1), colors.lightblue),
                        ('GRID', (0, 0), (-1, -1), 1, colors.black)
                    ]))

                    story.append(endpoint_table)
                    story.append(Spacer(1, 12))

            # Performance Recommendations Section (Additional value)
            if 'recommendations' in content:
                story.append(Paragraph("Recomendaciones de Rendimiento y Elementos de Acción", styles['Heading2']))
                recommendations = content['recommendations']

                if recommendations:
                    for i, rec in enumerate(recommendations, 1):
                        story.append(Paragraph(f"{i}. {rec}", styles['Normal']))
                        story.append(Spacer(1, 6))
                else:
                    story.append(Paragraph("El sistema funciona de manera óptima. No se requiere acción inmediata.", styles['Normal']))

                story.append(Spacer(1, 12))

            # Add detailed results
            if 'detailed_results' in content:
                story.append(PageBreak())
                story.append(Paragraph("Resultados Detallados de Pruebas", styles['Heading2']))
                
                for result in content['detailed_results']:
                    story.append(Paragraph(f"Escenario: {result.get('name', 'Desconocido')}", styles['Heading3']))

                    result_data = [
                        ['Métrica', 'Valor'],
                        ['Tiempo de Respuesta Promedio', f"{result.get('avg_response_time', 'N/A')} ms"],
                        ['Percentil 95', f"{result.get('p95_response_time', 'N/A')} ms"],
                        ['Total de Peticiones', str(result.get('total_requests', 'N/A'))],
                        ['Tasa de Éxito', f"{result.get('success_rate', 'N/A')}%"],
                        ['Peticiones por Segundo', f"{result.get('rps', 'N/A')}"],
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
            
            # Note: recommendations section already handled above in Spanish section
            # This duplicate section in English has been removed
            
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
        """Create enhanced response time chart with degradation analysis."""
        fig, ax = plt.subplots(figsize=(12, 7))

        # Extract data
        scenarios = [item['scenario'] for item in response_time_data]
        avg_times = [item['avg_response_time'] for item in response_time_data]
        p95_times = [item['p95_response_time'] for item in response_time_data]

        x = range(len(scenarios))

        # Plot response times
        ax.plot(x, avg_times, marker='o', label='Tiempo de Respuesta Promedio', linewidth=2, markersize=8)
        ax.plot(x, p95_times, marker='s', label='Percentil 95', linewidth=2, markersize=8)

        # Add degradation threshold lines (CU.3 requirement: show limits)
        if avg_times:
            baseline_avg = min(avg_times) if avg_times else 0
            degradation_threshold_avg = baseline_avg * 2  # 100% degradation
            critical_threshold_avg = baseline_avg * 3     # 200% degradation

            if degradation_threshold_avg > 0:
                ax.axhline(y=degradation_threshold_avg, color='orange', linestyle='--',
                          label=f'Umbral de Degradación ({degradation_threshold_avg:.0f}ms)', alpha=0.7)
                ax.axhline(y=critical_threshold_avg, color='red', linestyle='--',
                          label=f'Umbral Crítico ({critical_threshold_avg:.0f}ms)', alpha=0.7)

        # Highlight degradation points (CU.3 requirement: mark degradation points)
        for i, avg_time in enumerate(avg_times):
            if i > 0 and avg_time > avg_times[i-1] * 1.5:  # 50% increase = degradation
                ax.scatter(i, avg_time, color='red', s=100, marker='X',
                          label='Punto de Degradación' if i == 1 else "", zorder=5)

        ax.set_xlabel('Escenarios de Prueba (Carga Creciente)', fontsize=12)
        ax.set_ylabel('Tiempo de Respuesta (ms)', fontsize=12)
        ax.set_title('Análisis de Rendimiento - Tiempos de Respuesta\nDetección de Degradación del Rendimiento', fontsize=14, fontweight='bold')
        ax.set_xticks(x)
        ax.set_xticklabels([f'Escenario {i+1}' for i in x], rotation=45)
        ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        ax.grid(True, alpha=0.3)

        # Add performance annotations with summary
        summary_text = ""
        if len(avg_times) > 1:
            performance_change = ((avg_times[-1] - avg_times[0]) / avg_times[0] * 100) if avg_times[0] > 0 else 0
            min_time = min(avg_times)
            max_time = max(avg_times)
            avg_of_avgs = sum(avg_times) / len(avg_times)

            summary_text = f'Cambio de Rendimiento: {performance_change:+.1f}%\n'
            summary_text += f'Min: {min_time:.1f}ms | Max: {max_time:.1f}ms | Media: {avg_of_avgs:.1f}ms'

            # Determine trend
            if performance_change > 50:
                summary_text += '\nTendencia: Degradación Significativa ⚠'
            elif performance_change > 20:
                summary_text += '\nTendencia: Degradación Moderada'
            elif performance_change > -10:
                summary_text += '\nTendencia: Estable ✓'
            else:
                summary_text += '\nTendencia: Mejora'

            ax.text(0.02, 0.98, summary_text,
                   transform=ax.transAxes, verticalalignment='top',
                   bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.8),
                   fontsize=9)

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

        # Color bars based on performance (green=high, yellow=medium, red=low)
        max_rps = max(rps) if rps else 1
        colors_list = ['green' if r > max_rps * 0.7 else 'orange' if r > max_rps * 0.4 else 'red' for r in rps]

        bars = ax.bar(range(len(scenarios)), rps, color=colors_list, alpha=0.7)

        ax.set_xlabel('Escenarios de Prueba', fontsize=12)
        ax.set_ylabel('Peticiones por Segundo', fontsize=12)
        ax.set_title('Análisis de Capacidad de Procesamiento (Throughput)', fontsize=14, fontweight='bold')
        ax.set_xticks(range(len(scenarios)))
        ax.set_xticklabels([f'Escenario {i+1}' for i in range(len(scenarios))], rotation=45)
        ax.grid(True, alpha=0.3, axis='y')

        # Add value labels on bars
        for bar, value in zip(bars, rps):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{value:.1f}', ha='center', va='bottom', fontsize=9)

        # Add summary annotation
        if len(rps) > 1:
            avg_rps = sum(rps) / len(rps)
            max_rps_val = max(rps)
            min_rps_val = min(rps)
            throughput_change = ((rps[-1] - rps[0]) / rps[0] * 100) if rps[0] > 0 else 0

            summary_text = f'Promedio: {avg_rps:.1f} req/s\n'
            summary_text += f'Máximo: {max_rps_val:.1f} req/s | Mínimo: {min_rps_val:.1f} req/s\n'
            summary_text += f'Cambio: {throughput_change:+.1f}%'

            if throughput_change < -20:
                summary_text += '\nCapacidad: Reducción Significativa ⚠'
            elif throughput_change > 20:
                summary_text += '\nCapacidad: Incremento ✓'
            else:
                summary_text += '\nCapacidad: Estable'

            ax.text(0.02, 0.98, summary_text,
                   transform=ax.transAxes, verticalalignment='top',
                   bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.8),
                   fontsize=9)

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

        # Add threshold lines
        ax.axhline(y=5, color='orange', linestyle='--', label='Umbral Aceptable (5%)', alpha=0.7)
        ax.axhline(y=10, color='red', linestyle='--', label='Umbral Crítico (10%)', alpha=0.7)

        ax.set_xlabel('Escenarios de Prueba', fontsize=12)
        ax.set_ylabel('Tasa de Errores (%)', fontsize=12)
        ax.set_title('Análisis de Tasa de Errores', fontsize=14, fontweight='bold')
        ax.set_xticks(range(len(scenarios)))
        ax.set_xticklabels([f'Escenario {i+1}' for i in range(len(scenarios))], rotation=45)
        ax.set_ylim(0, max(error_rates) * 1.1 if error_rates else 100)
        # Add value labels on bars
        for bar, value in zip(bars, error_rates):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{value:.1f}%', ha='center', va='bottom', fontsize=9)

        # Add summary annotation
        if error_rates:
            avg_error = sum(error_rates) / len(error_rates)
            max_error = max(error_rates)
            critical_scenarios = sum(1 for rate in error_rates if rate > 10)

            summary_text = f'Promedio de Errores: {avg_error:.1f}%\n'
            summary_text += f'Máximo: {max_error:.1f}%\n'

            if critical_scenarios > 0:
                summary_text += f'Escenarios Críticos: {critical_scenarios} ⚠'
            elif max_error > 5:
                summary_text += 'Estado: Requiere Atención'
            else:
                summary_text += 'Estado: Aceptable ✓'

            ax.text(0.02, 0.98, summary_text,
                   transform=ax.transAxes, verticalalignment='top',
                   bbox=dict(boxstyle='round', facecolor='lightcoral', alpha=0.8),
                   fontsize=9)

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
                'title': f"Informe de Pruebas de Rendimiento - LoadTester",
                'executive_summary': executive_summary.get('summary', ''),
                'test_configuration': {
                    'total_scenarios': len(test_results),
                    'total_endpoints': job_info.get('total_endpoints', 'N/A'),
                    'created_at': job_info.get('created_at', '').strftime('%Y-%m-%d %H:%M:%S') if job_info.get('created_at') else 'N/A',
                    'test_duration': job_info.get('test_duration', 0),
                    'k6_version': 'v0.47.0',
                    'load_testing_strategy': 'Pruebas de Carga Progresivas',
                },
                'charts': chart_paths,
                'detailed_results': self._format_detailed_results(test_results),
                'degradation_analysis': degradation_points,
                'performance_analysis': analysis,
                'endpoint_summary': self._generate_endpoint_summary(test_results),
                'recommendations': await self._generate_performance_recommendations(test_results),
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
            Escribe un resumen ejecutivo profesional en CASTELLANO para un informe de pruebas de carga con los siguientes datos:

            Resumen de Resultados:
            - Total de Escenarios de Prueba: {len(test_results)}
            - Total de Peticiones: {total_requests}
            - Total de Errores: {total_errors}
            - Tiempo de Respuesta Promedio: {avg_response_time:.2f} ms
            - Tasa de Error: {(total_errors / total_requests * 100) if total_requests > 0 else 0:.2f}%

            El resumen debe (2-3 párrafos):
            1. Resumir la ejecución de las pruebas
            2. Destacar los hallazgos clave de rendimiento
            3. Mencionar puntos de degradación encontrados
            4. Proporcionar recomendaciones de alto nivel

            IMPORTANTE:
            - Escribe SOLO en castellano
            - NO uses formato markdown (nada de ##, **, etc.)
            - Enfócate en aspectos empresariales, no técnicos
            - Si no hay datos (total_requests = 0), indica que no se pudo generar carga y recomienda revisar la configuración
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
                f"Alta tasa de errores detectada en {len(high_error_results)} escenarios. "
                "Considere optimizar la capacidad del servidor o revisar el código de la aplicación."
            )

        # Check for response time degradation
        response_times = [r.avg_response_time_ms for r in test_results if r.avg_response_time_ms]
        if len(response_times) > 1:
            baseline = response_times[0]
            degraded_scenarios = [i for i, rt in enumerate(response_times) if rt > baseline * 3]

            if degraded_scenarios:
                recommendations.append(
                    f"Degradación en tiempos de respuesta detectada a partir del escenario {degraded_scenarios[0] + 1}. "
                    "Esto indica que el sistema alcanzó sus límites de rendimiento."
                )

        # Check for throughput issues
        throughputs = [r.requests_per_second for r in test_results if r.requests_per_second]
        if throughputs and any(t < max(throughputs) * 0.5 for t in throughputs[-3:]):
            recommendations.append(
                "Degradación de throughput observada en los escenarios finales. "
                "Considere implementar balanceo de carga o estrategias de escalado."
            )

        if not recommendations:
            recommendations.append(
                "No se detectó degradación significativa del rendimiento. "
                "El sistema funcionó dentro de parámetros aceptables para la carga probada."
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
                'scenario': f'Escenario {i+1}',
                'avg_response_time': result.avg_response_time_ms or 0,
                'p95_response_time': result.p95_response_time_ms or 0,
            })

            chart_data['throughput'].append({
                'scenario': f'Escenario {i+1}',
                'requests_per_second': result.requests_per_second or 0,
            })

            chart_data['error_rates'].append({
                'scenario': f'Escenario {i+1}',
                'error_rate': result.error_rate_percent,
            })
        
        return chart_data
    
    def _format_detailed_results(self, test_results: List[TestResult]) -> List[Dict]:
        """Format detailed results for PDF table."""
        detailed_results = []
        
        for i, result in enumerate(test_results):
            detailed_results.append({
                'name': f'Escenario {i+1}',
                'avg_response_time': f"{result.avg_response_time_ms or 0:.2f}",
                'p95_response_time': f"{result.p95_response_time_ms or 0:.2f}",
                'total_requests': result.total_requests or 0,
                'success_rate': f"{result.success_rate_percent or 0:.2f}",
                'rps': f"{result.requests_per_second or 0:.2f}",
            })
        
        return detailed_results

    def _generate_endpoint_summary(self, test_results: List[TestResult]) -> Dict:
        """Generate endpoint-specific summary for CU.3 compliance."""
        if not test_results:
            return {'endpoints': [], 'summary': 'No test results available'}

        endpoint_summary = {
            'total_endpoints_tested': len(test_results),
            'endpoints': [],
            'summary': ''
        }

        for i, result in enumerate(test_results):
            endpoint_info = {
                'endpoint': f'Endpoint {i+1}',  # In real implementation, this would be actual endpoint path
                'method': 'GET',  # In real implementation, this would be actual HTTP method
                'total_requests': result.total_requests or 0,
                'success_rate': result.success_rate_percent or 0,
                'avg_response_time': result.avg_response_time_ms or 0,
                'p95_response_time': result.p95_response_time_ms or 0,
                'performance_classification': self._classify_performance(result),
                'degradation_detected': result.avg_response_time_ms > 500 if result.avg_response_time_ms else False
            }
            endpoint_summary['endpoints'].append(endpoint_info)

        # Generate summary text
        healthy_endpoints = sum(1 for ep in endpoint_summary['endpoints'] if ep['performance_classification'] == 'Healthy')
        degraded_endpoints = sum(1 for ep in endpoint_summary['endpoints'] if ep['degradation_detected'])

        endpoint_summary['summary'] = (
            f"Tested {endpoint_summary['total_endpoints_tested']} endpoints. "
            f"{healthy_endpoints} performing within acceptable limits. "
            f"{degraded_endpoints} showing performance degradation."
        )

        return endpoint_summary

    def _classify_performance(self, result: TestResult) -> str:
        """Classify endpoint performance based on response times and error rates."""
        if not result.avg_response_time_ms:
            return 'Desconocido'

        # Critical if error rate is very high
        if result.error_rate_percent >= 50:
            return 'Crítico'

        # Degraded if error rate is moderate
        if result.error_rate_percent >= 10:
            return 'Degradado'

        # Otherwise, classify by response time
        if result.avg_response_time_ms < 200:
            return 'Excelente'
        elif result.avg_response_time_ms < 500:
            return 'Bueno'
        elif result.avg_response_time_ms < 1000:
            return 'Degradado'
        else:
            return 'Crítico'

    async def _generate_performance_recommendations(self, test_results: List[TestResult]) -> List[str]:
        """Generate performance recommendations based on test results."""
        recommendations = []

        if not test_results:
            return ["No hay resultados de prueba disponibles para análisis."]

        # Analyze average response times
        avg_times = [result.avg_response_time_ms for result in test_results if result.avg_response_time_ms]

        if avg_times:
            max_avg_time = max(avg_times)
            if max_avg_time > 1000:
                recommendations.append(
                    f"Crítico: Los tiempos de respuesta superan los 1000ms (máx: {max_avg_time:.1f}ms). "
                    "Considere optimizar las consultas a base de datos, añadir caché o escalar la infraestructura."
                )
            elif max_avg_time > 500:
                recommendations.append(
                    f"Advertencia: Los tiempos de respuesta se acercan al umbral de 500ms (máx: {max_avg_time:.1f}ms). "
                    "Monitoree el rendimiento y considere optimización preventiva."
                )

        # Analyze success rates
        success_rates = [result.success_rate_percent for result in test_results if result.success_rate_percent is not None]

        if success_rates:
            min_success_rate = min(success_rates)
            if min_success_rate < 95:
                recommendations.append(
                    f"Problema de Tasa de Errores: La tasa de éxito cayó al {min_success_rate:.1f}%. "
                    "Investigue los logs de errores e implemente manejo de errores apropiado y mecanismos de reintento."
                )

        # Analyze throughput trends
        rps_values = [result.requests_per_second for result in test_results if result.requests_per_second]

        if len(rps_values) > 1:
            throughput_decline = ((rps_values[-1] - rps_values[0]) / rps_values[0] * 100) if rps_values[0] > 0 else 0
            if throughput_decline < -20:
                recommendations.append(
                    f"Caída de Throughput: Reducción del {abs(throughput_decline):.1f}% en peticiones/segundo. "
                    "El sistema puede estar alcanzando sus límites de capacidad. Considere escalado horizontal."
                )

        # Add general recommendations if no issues found
        if not recommendations:
            recommendations.extend([
                "El sistema está funcionando dentro de parámetros aceptables.",
                "Continúe monitoreando durante períodos de uso intenso.",
                "Considere implementar líneas base de rendimiento para comparaciones futuras.",
                "Configure alertas automáticas para umbrales de tiempo de respuesta y tasa de errores."
            ])

        return recommendations