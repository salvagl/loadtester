"""
LoadTester Frontend - Streamlit Application
Main interface for LoadTester application
"""

import os
import time
from typing import Dict, List, Optional

import pandas as pd
import requests
import streamlit as st
from streamlit_option_menu import option_menu

from components.openapi_parser_component import OpenAPIParserComponent
from components.endpoint_selector_component import EndpointSelectorComponent
from components.test_configurator_component import TestConfiguratorComponent
from components.results_viewer_component import ResultsViewerComponent

# Configuration
BACKEND_URL = os.getenv("BACKEND_URL", "http://backend:8000")

# Page configuration
st.set_page_config(
    page_title="LoadTester",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .section-header {
        font-size: 1.5rem;
        color: #2c3e50;
        margin-top: 2rem;
        margin-bottom: 1rem;
        border-bottom: 2px solid #1f77b4;
        padding-bottom: 0.5rem;
    }
    .info-box {
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
        background-color: #f8f9fa;
        margin: 1rem 0;
    }
    .success-box {
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #28a745;
        background-color: #d4edda;
        margin: 1rem 0;
    }
    .warning-box {
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #ffc107;
        background-color: #fff3cd;
        margin: 1rem 0;
    }
    .error-box {
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #dc3545;
        background-color: #f8d7da;
        margin: 1rem 0;
    }
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 0.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border: 1px solid #e0e0e0;
    }
</style>
""", unsafe_allow_html=True)

def initialize_session_state():
    """Initialize Streamlit session state variables."""
    if 'openapi_spec' not in st.session_state:
        st.session_state.openapi_spec = None
    if 'parsed_spec' not in st.session_state:
        st.session_state.parsed_spec = None
    if 'available_endpoints' not in st.session_state:
        st.session_state.available_endpoints = []
    if 'selected_endpoints' not in st.session_state:
        st.session_state.selected_endpoints = []
    if 'test_configuration' not in st.session_state:
        st.session_state.test_configuration = {}
    if 'current_job_id' not in st.session_state:
        st.session_state.current_job_id = None
    if 'job_status' not in st.session_state:
        st.session_state.job_status = None

def render_header():
    """Render application header."""
    st.markdown('<h1 class="main-header">🚀 LoadTester</h1>', unsafe_allow_html=True)
    st.markdown(
        '<p style="text-align: center; color: #666; font-size: 1.1rem;">'
        'Automated API Load Testing with OpenAPI Specification'
        '</p>',
        unsafe_allow_html=True
    )

def render_sidebar():
    """Render application sidebar with navigation."""
    with st.sidebar:
        st.image("https://via.placeholder.com/200x80/1f77b4/white?text=LoadTester", width=200)
        
        selected = option_menu(
            menu_title="Navigation",
            options=["Setup", "Configure", "Execute", "Results", "History"],
            icons=["gear", "sliders", "play-circle", "bar-chart", "clock-history"],
            menu_icon="list",
            default_index=0,
            styles={
                "container": {"padding": "0!important", "background-color": "#fafafa"},
                "icon": {"color": "#1f77b4", "font-size": "18px"},
                "nav-link": {
                    "font-size": "16px",
                    "text-align": "left",
                    "margin": "0px",
                    "--hover-color": "#eee"
                },
                "nav-link-selected": {"background-color": "#1f77b4"},
            }
        )
        
        st.markdown("---")
        
        # System status
        st.markdown("### System Status")
        try:
            response = requests.get(f"{BACKEND_URL}/health", timeout=5)
            if response.status_code == 200:
                st.success("✅ Backend Online")
            else:
                st.error("❌ Backend Error")
        except:
            st.error("❌ Backend Offline")
        
        # Quick stats
        if st.session_state.current_job_id:
            st.markdown("### Current Job")
            st.info(f"Job ID: {st.session_state.current_job_id[:8]}...")
            
            if st.session_state.job_status:
                status = st.session_state.job_status.get('status', 'UNKNOWN')
                progress = st.session_state.job_status.get('progress', 0)
                
                if status == "RUNNING":
                    st.progress(progress / 100)
                    st.write(f"Progress: {progress:.1f}%")
                elif status == "FINISHED":
                    st.success("✅ Completed")
                elif status == "FAILED":
                    st.error("❌ Failed")
    
    return selected

def render_setup_page():
    """Render OpenAPI specification setup page."""
    st.markdown('<h2 class="section-header">📋 Step 1: OpenAPI Specification</h2>', unsafe_allow_html=True)
    
    # Create OpenAPI parser component
    openapi_component = OpenAPIParserComponent(backend_url=BACKEND_URL)
    
    # Load OpenAPI specification
    spec_result = openapi_component.render()
    
    if spec_result and spec_result.get('success'):
        st.session_state.openapi_spec = spec_result['spec_content']
        st.session_state.parsed_spec = spec_result['parsed_spec']
        st.session_state.available_endpoints = spec_result['endpoints']
        
        st.markdown('<div class="success-box">✅ OpenAPI specification loaded successfully!</div>', 
                   unsafe_allow_html=True)
        
        # Show API information
        if st.session_state.parsed_spec:
            info = st.session_state.parsed_spec.get('info', {})
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("API Title", info.get('title', 'N/A'))
            with col2:
                st.metric("Version", info.get('version', 'N/A'))
            with col3:
                st.metric("Endpoints", len(st.session_state.available_endpoints))
        
        # Preview endpoints
        if st.session_state.available_endpoints:
            st.markdown("### Available Endpoints")
            
            endpoints_df = pd.DataFrame([
                {
                    'Method': ep.get('method', '').upper(),
                    'Path': ep.get('path', ''),
                    'Summary': ep.get('summary', '')[:50] + '...' if ep.get('summary', '') else 'N/A'
                }
                for ep in st.session_state.available_endpoints
            ])
            
            st.dataframe(endpoints_df, use_container_width=True)

def render_configure_page():
    """Render endpoint selection and configuration page."""
    st.markdown('<h2 class="section-header">⚙️ Step 2: Configure Test Endpoints</h2>', unsafe_allow_html=True)
    
    if not st.session_state.available_endpoints:
        st.markdown('<div class="warning-box">⚠️ Please load an OpenAPI specification first in the Setup page.</div>', 
                   unsafe_allow_html=True)
        return
    
    # Create endpoint selector component
    selector_component = EndpointSelectorComponent()
    selected_endpoints = selector_component.render(st.session_state.available_endpoints)
    
    if selected_endpoints:
        st.session_state.selected_endpoints = selected_endpoints
        
        # Create test configurator component
        st.markdown("### Test Configuration")
        configurator_component = TestConfiguratorComponent()
        test_config = configurator_component.render(selected_endpoints)
        
        if test_config:
            st.session_state.test_configuration = test_config
            
            st.markdown('<div class="success-box">✅ Test configuration completed!</div>', 
                       unsafe_allow_html=True)

def render_execute_page():
    """Render test execution page."""
    st.markdown('<h2 class="section-header">▶️ Step 3: Execute Load Test</h2>', unsafe_allow_html=True)
    
    if not st.session_state.selected_endpoints:
        st.markdown('<div class="warning-box">⚠️ Please configure test endpoints first.</div>', 
                   unsafe_allow_html=True)
        return
    
    # Test summary
    st.markdown("### Test Summary")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Selected Endpoints", len(st.session_state.selected_endpoints))
    with col2:
        total_users = sum(ep.get('expected_concurrent_users', 0) for ep in st.session_state.selected_endpoints)
        st.metric("Total Users", total_users)
    with col3:
        total_volumetry = sum(ep.get('expected_volumetry', 0) for ep in st.session_state.selected_endpoints)
        st.metric("Total Req/Min", total_volumetry)
    
    # Configuration summary
    with st.expander("Configuration Details"):
        for i, endpoint in enumerate(st.session_state.selected_endpoints):
            st.write(f"**{endpoint['method'].upper()} {endpoint['path']}**")
            st.write(f"- Expected Users: {endpoint.get('expected_concurrent_users', 'N/A')}")
            st.write(f"- Expected Volumetry: {endpoint.get('expected_volumetry', 'N/A')} req/min")
            st.write(f"- Timeout: {endpoint.get('timeout_ms', 30000)} ms")
            if i < len(st.session_state.selected_endpoints) - 1:
                st.write("---")
    
    # Execute button
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🚀 Start Load Test", type="primary", use_container_width=True):
            execute_load_test()
    
    # Show job status if running
    if st.session_state.current_job_id:
        render_job_status()

def execute_load_test():
    """Execute the load test."""
    try:
        # Prepare request payload
        payload = {
            "api_spec": st.session_state.openapi_spec,
            "selected_endpoints": st.session_state.selected_endpoints,
            "global_auth": st.session_state.test_configuration.get('global_auth'),
            "callback_url": st.session_state.test_configuration.get('callback_url'),
            "test_name": st.session_state.test_configuration.get('test_name', 'LoadTester Job')
        }
        
        # Make API request
        with st.spinner("Creating load test job..."):
            response = requests.post(
                f"{BACKEND_URL}/api/v1/load-test",
                json=payload,
                timeout=30
            )
        
        if response.status_code == 202:
            result = response.json()
            st.session_state.current_job_id = result['job_id']
            st.success(f"✅ Load test started! Job ID: {result['job_id']}")
            
            # Auto-refresh to show status
            time.sleep(1)
            st.rerun()
        else:
            st.error(f"❌ Failed to start load test: {response.text}")
    
    except Exception as e:
        st.error(f"❌ Error starting load test: {str(e)}")

def render_job_status():
    """Render current job status."""
    try:
        response = requests.get(f"{BACKEND_URL}/api/v1/status/{st.session_state.current_job_id}")
        
        if response.status_code == 200:
            status_data = response.json()
            st.session_state.job_status = status_data
            
            status = status_data.get('status', 'UNKNOWN')
            progress = status_data.get('progress', 0)
            
            st.markdown("### Job Status")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                if status == "PENDING":
                    st.info(f"📋 Status: {status}")
                elif status == "RUNNING":
                    st.warning(f"⏳ Status: {status}")
                elif status == "FINISHED":
                    st.success(f"✅ Status: {status}")
                elif status == "FAILED":
                    st.error(f"❌ Status: {status}")
            
            with col2:
                st.metric("Progress", f"{progress:.1f}%")
            
            with col3:
                if status_data.get('report_url'):
                    if st.button("📄 Download Report"):
                        download_report(st.session_state.current_job_id)
            
            # Progress bar
            if status == "RUNNING":
                st.progress(progress / 100)
                
                # Auto-refresh every 5 seconds
                time.sleep(5)
                st.rerun()
            
            # Show error if failed
            if status == "FAILED" and status_data.get('error_message'):
                st.error(f"Error: {status_data['error_message']}")
    
    except Exception as e:
        st.error(f"Error getting job status: {str(e)}")

def download_report(job_id: str):
    """Download the test report."""
    try:
        response = requests.get(f"{BACKEND_URL}/api/v1/report/{job_id}")
        
        if response.status_code == 200:
            st.download_button(
                label="📥 Download PDF Report",
                data=response.content,
                file_name=f"loadtest_report_{job_id}.pdf",
                mime="application/pdf"
            )
        else:
            st.error("Failed to download report")
    
    except Exception as e:
        st.error(f"Error downloading report: {str(e)}")

def render_results_page():
    """Render test results page."""
    st.markdown('<h2 class="section-header">📊 Test Results</h2>', unsafe_allow_html=True)
    
    # Create results viewer component
    results_component = ResultsViewerComponent(backend_url=BACKEND_URL)
    results_component.render()

def render_history_page():
    """Render test history page."""
    st.markdown('<h2 class="section-header">🕒 Test History</h2>', unsafe_allow_html=True)
    
    try:
        response = requests.get(f"{BACKEND_URL}/api/v1/reports")
        
        if response.status_code == 200:
            reports_data = response.json()
            reports = reports_data.get('reports', [])
            
            if reports:
                st.markdown(f"Found {len(reports)} test reports")
                
                for report in reports:
                    with st.expander(f"Report: {report['job_id'][:8]}... - {report['filename']}"):
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.write(f"**Size:** {report['size'] / 1024:.1f} KB")
                        with col2:
                            created = pd.to_datetime(report['created_at'], unit='s')
                            st.write(f"**Created:** {created.strftime('%Y-%m-%d %H:%M')}")
                        with col3:
                            if st.button(f"Download", key=f"download_{report['job_id']}"):
                                download_report(report['job_id'])
            else:
                st.info("No test reports found.")
        else:
            st.error("Failed to load test history")
    
    except Exception as e:
        st.error(f"Error loading history: {str(e)}")

def main():
    """Main application function."""
    initialize_session_state()
    render_header()
    
    # Render sidebar and get selected page
    selected_page = render_sidebar()
    
    # Render selected page
    if selected_page == "Setup":
        render_setup_page()
    elif selected_page == "Configure":
        render_configure_page()
    elif selected_page == "Execute":
        render_execute_page()
    elif selected_page == "Results":
        render_results_page()
    elif selected_page == "History":
        render_history_page()

if __name__ == "__main__":
    main()