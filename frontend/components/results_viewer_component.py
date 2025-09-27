"""
Results Viewer Component
Streamlit component for viewing load test results and metrics
"""

from typing import Dict, List, Optional

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st
from plotly.subplots import make_subplots


class ResultsViewerComponent:
    """Component for viewing test results and metrics."""
    
    def __init__(self, backend_url: str):
        self.backend_url = backend_url
    
    def render(self):
        """Render the results viewer component."""
        st.markdown("View and analyze load test results:")
        
        # Current job results
        if st.session_state.get('current_job_id'):
            self._render_current_job_results()
        
        # Historical results
        self._render_historical_results()
    
    def _render_current_job_results(self):
        """Render results for the current job."""
        job_id = st.session_state.current_job_id
        
        st.markdown("### 🔄 Current Job Results")
        
        try:
            # Get job status
            status_response = requests.get(f"{self.backend_url}/api/v1/status/{job_id}")
            
            if status_response.status_code == 200:
                status_data = status_response.json()
                
                if status_data.get('status') == 'FINISHED':
                    # Show completion message
                    st.success("✅ Load test completed successfully!")
                    
                    # Provide download link
                    col1, col2, col3 = st.columns([1, 2, 1])
                    with col2:
                        if st.button("📄 Download Full Report", type="primary", use_container_width=True):
                            self._download_report(job_id)
                    
                    # Show quick metrics if available
                    self._render_quick_metrics(job_id)
                
                elif status_data.get('status') == 'RUNNING':
                    progress = status_data.get('progress', 0)
                    
                    st.info(f"⏳ Test in progress... {progress:.1f}% complete")
                    st.progress(progress / 100)
                    
                    # Auto-refresh
                    if st.button("🔄 Refresh Status"):
                        st.rerun()
                
                elif status_data.get('status') == 'FAILED':
                    st.error(f"❌ Test failed: {status_data.get('error_message', 'Unknown error')}")
                
                else:
                    st.info(f"📋 Test status: {status_data.get('status', 'Unknown')}")
            
            else:
                st.error(f"Failed to get job status: {status_response.text}")
        
        except Exception as e:
            st.error(f"Error getting job results: {str(e)}")
    
    def _render_historical_results(self):
        """Render historical test results."""
        st.markdown("### 📚 Historical Results")
        
        try:
            # Get available reports
            reports_response = requests.get(f"{self.backend_url}/api/v1/reports")
            
            if reports_response.status_code == 200:
                reports_data = reports_response.json()
                reports = reports_data.get('reports', [])
                
                if reports:
                    # Create reports table
                    reports_df = pd.DataFrame(reports)
                    reports_df['created_at'] = pd.to_datetime(reports_df['created_at'], unit='s')
                    reports_df['size_mb'] = (reports_df['size'] / (1024 * 1024)).round(2)
                    
                    # Display table
                    st.dataframe(
                        reports_df[['job_id', 'created_at', 'size_mb']].rename(columns={
                            'job_id': 'Job ID',
                            'created_at': 'Created At',
                            'size_mb': 'Size (MB)'
                        }),
                        use_container_width=True
                    )
                    
                    # Download buttons
                    st.markdown("**Download Reports:**")
                    for report in reports[:5]:  # Show latest 5 reports
                        col1, col2, col3 = st.columns([3, 1, 1])
                        
                        with col1:
                            created = pd.to_datetime(report['created_at'], unit='s')
                            st.write(f"Job: {report['job_id'][:8]}... - {created.strftime('%Y-%m-%d %H:%M')}")
                        
                        with col2:
                            st.write(f"{report['size'] / 1024:.1f} KB")
                        
                        with col3:
                            if st.button("📥", key=f"download_{report['job_id']}", help="Download report"):
                                self._download_report(report['job_id'])
                
                else:
                    st.info("No historical reports found.")
            
            else:
                st.error("Failed to load historical results")
        
        except Exception as e:
            st.error(f"Error loading historical results: {str(e)}")
    
    def _download_report(self, job_id: str):
        """Download a test report."""
        try:
            response = requests.get(f"{self.backend_url}/api/v1/report/{job_id}")
            
            if response.status_code == 200:
                st.download_button(
                    label=f"📥 Download Report {job_id[:8]}...",
                    data=response.content,
                    file_name=f"loadtest_report_{job_id}.pdf",
                    mime="application/pdf",
                    key=f"download_btn_{job_id}"
                )
            else:
                st.error(f"Failed to download report: {response.text}")
        
        except Exception as e:
            st.error(f"Error downloading report: {str(e)}")
    
    def _render_quick_metrics(self, job_id: str):
        """Render quick metrics for a completed job."""
        try:
            # This would typically get metrics from the backend
            # For now, show placeholder metrics
            
            st.markdown("### 📊 Quick Metrics")
            
            # Mock data for demonstration
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    label="Total Requests",
                    value="1,247",
                    delta="98.5% success"
                )
            
            with col2:
                st.metric(
                    label="Avg Response Time",
                    value="245 ms",
                    delta="-12 ms"
                )
            
            with col3:
                st.metric(
                    label="Peak RPS",
                    value="45.2",
                    delta="+12.3"
                )
            
            with col4:
                st.metric(
                    label="Test Duration",
                    value="5.2 min",
                    delta="Normal"
                )
            
            # Mock performance charts
            self._render_mock_charts()
        
        except Exception as e:
            st.error(f"Error rendering metrics: {str(e)}")
    
    def _render_mock_charts(self):
        """Render mock performance charts for demonstration."""
        st.markdown("### 📈 Performance Charts")
        
        # Generate mock data
        import numpy as np
        
        scenarios = [f"Scenario {i+1}" for i in range(6)]
        response_times = [120, 140, 180, 250, 340, 450]
        error_rates = [0.5, 1.2, 2.1, 5.8, 12.3, 25.6]
        throughput = [45, 52, 48, 42, 35, 28]
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Response time chart
            fig_response = px.line(
                x=scenarios,
                y=response_times,
                title="Response Time by Scenario",
                labels={'x': 'Test Scenario', 'y': 'Response Time (ms)'}
            )
            fig_response.add_hline(y=response_times[0] * 5, line_dash="dash", 
                                 annotation_text="Degradation Threshold")
            st.plotly_chart(fig_response, use_container_width=True)
        
        with col2:
            # Error rate chart
            fig_error = px.bar(
                x=scenarios,
                y=error_rates,
                title="Error Rate by Scenario",
                labels={'x': 'Test Scenario', 'y': 'Error Rate (%)'},
                color=error_rates,
                color_continuous_scale='Reds'
            )
            fig_error.add_hline(y=10, line_dash="dash", 
                              annotation_text="Critical Threshold")
            st.plotly_chart(fig_error, use_container_width=True)
        
        # Throughput chart
        fig_throughput = px.area(
            x=scenarios,
            y=throughput,
            title="Throughput Performance",
            labels={'x': 'Test Scenario', 'y': 'Requests per Second'}
        )
        st.plotly_chart(fig_throughput, use_container_width=True)
        
        # Performance summary table
        st.markdown("### 📋 Scenario Summary")
        
        summary_df = pd.DataFrame({
            'Scenario': scenarios,
            'Avg Response Time (ms)': response_times,
            'Error Rate (%)': error_rates,
            'Throughput (RPS)': throughput,
            'Status': ['✅ Pass', '✅ Pass', '✅ Pass', '⚠️ Warning', '❌ Degraded', '❌ Failed']
        })
        
        st.dataframe(summary_df, use_container_width=True)
        
        # Key findings
        with st.expander("🔍 Key Findings"):
            st.markdown("""
            **Performance Analysis:**
            - ✅ System performed well up to Scenario 3 (normal load)
            - ⚠️ Degradation started at Scenario 4 (high load)
            - ❌ Critical issues emerged at Scenario 5-6 (extreme load)
            
            **Recommendations:**
            - Consider optimizing for loads above 180ms response time
            - Implement error handling for high-load scenarios
            - Scale infrastructure to handle peak loads
            """)
    
    def _render_live_metrics(self, job_id: str):
        """Render live metrics during test execution."""
        # This would show real-time metrics during test execution
        # For now, just a placeholder
        
        st.markdown("### ⚡ Live Metrics")
        
        # Mock live data
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Current RPS", "42.3", "+2.1")
        
        with col2:
            st.metric("Active Users", "28", "+5")
        
        with col3:
            st.metric("Current Scenario", "3/8", "Running")
        
        # Live response time chart (placeholder)
        import numpy as np
        import time
        
        if 'live_data' not in st.session_state:
            st.session_state.live_data = []
        
        # Simulate new data point
        current_time = time.time()
        new_point = {
            'timestamp': current_time,
            'response_time': np.random.normal(200, 50),
            'error_rate': max(0, np.random.normal(2, 1))
        }
        
        st.session_state.live_data.append(new_point)
        
        # Keep only last 50 points
        if len(st.session_state.live_data) > 50:
            st.session_state.live_data = st.session_state.live_data[-50:]
        
        if st.session_state.live_data:
            df = pd.DataFrame(st.session_state.live_data)
            
            fig = px.line(
                df,
                x='timestamp',
                y='response_time',
                title="Live Response Time",
                labels={'timestamp': 'Time', 'response_time': 'Response Time (ms)'}
            )
            
            st.plotly_chart(fig, use_container_width=True)