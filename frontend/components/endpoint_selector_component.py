"""
Endpoint Selector Component
Streamlit component for selecting and configuring API endpoints for testing
"""

from typing import Dict, List, Optional

import pandas as pd
import streamlit as st


class EndpointSelectorComponent:
    """Component for selecting endpoints to test."""
    
    def render(self, available_endpoints: List[Dict]) -> Optional[List[Dict]]:
        """Render the endpoint selector component."""
        if not available_endpoints:
            st.warning("No endpoints available for selection.")
            return None
        
        st.markdown("Select the endpoints you want to test:")
        
        # Filter options
        col1, col2 = st.columns(2)
        
        with col1:
            # Method filter
            available_methods = list(set(ep.get('method', '').upper() for ep in available_endpoints))
            method_filter = st.multiselect(
                "Filter by HTTP Method:",
                options=available_methods,
                default=available_methods,
                help="Select which HTTP methods to include"
            )
        
        with col2:
            # Path filter
            path_filter = st.text_input(
                "Filter by Path (contains):",
                placeholder="e.g., /users, /api/v1",
                help="Enter text that should be contained in the path"
            )
        
        # Apply filters
        filtered_endpoints = self._apply_filters(
            available_endpoints, 
            method_filter, 
            path_filter
        )
        
        if not filtered_endpoints:
            st.warning("No endpoints match the current filters.")
            return None
        
        # Display endpoints for selection
        st.markdown(f"**{len(filtered_endpoints)} endpoints available:**")
        
        selected_endpoints = []
        
        # Use checkbox selection with expandable details
        for i, endpoint in enumerate(filtered_endpoints):
            method = endpoint.get('method', '').upper()
            path = endpoint.get('path', '')
            summary = endpoint.get('summary', '')
            
            # Create a unique key for each endpoint
            endpoint_key = f"{method}_{path}_{i}"
            
            col1, col2 = st.columns([1, 4])
            
            with col1:
                selected = st.checkbox(
                    f"{method}",
                    key=f"select_{endpoint_key}",
                    help=f"Select {method} {path} for testing"
                )
            
            with col2:
                if selected:
                    with st.expander(f"🔧 Configure {method} {path}", expanded=True):
                        endpoint_config = self._render_endpoint_configuration(endpoint, endpoint_key)
                        if endpoint_config:
                            selected_endpoints.append(endpoint_config)
                else:
                    st.write(f"**{path}**")
                    if summary:
                        st.caption(summary)
        
        if selected_endpoints:
            # Summary of selection
            st.markdown("---")
            st.markdown("### Selection Summary")
            
            summary_df = pd.DataFrame([
                {
                    'Method': ep['method'].upper(),
                    'Path': ep['path'],
                    'Users': ep.get('expected_concurrent_users', 'Not set'),
                    'Req/Min': ep.get('expected_volumetry', 'Not set'),
                    'Auth': ep.get('auth', {}).get('type', 'None') if ep.get('auth') else 'None'
                }
                for ep in selected_endpoints
            ])
            
            st.dataframe(summary_df, use_container_width=True)
            
            return selected_endpoints
        
        return None
    
    def _apply_filters(
        self, 
        endpoints: List[Dict], 
        method_filter: List[str], 
        path_filter: str
    ) -> List[Dict]:
        """Apply filters to endpoint list."""
        filtered = endpoints
        
        # Apply method filter
        if method_filter:
            filtered = [
                ep for ep in filtered 
                if ep.get('method', '').upper() in method_filter
            ]
        
        # Apply path filter
        if path_filter:
            filtered = [
                ep for ep in filtered 
                if path_filter.lower() in ep.get('path', '').lower()
            ]
        
        return filtered
    
    def _render_endpoint_configuration(self, endpoint: Dict, endpoint_key: str) -> Optional[Dict]:
        """Render configuration options for a specific endpoint."""
        method = endpoint.get('method', '').upper()
        path = endpoint.get('path', '')
        
        # Basic configuration
        col1, col2 = st.columns(2)
        
        with col1:
            expected_volumetry = st.number_input(
                "Expected Requests/Min:",
                min_value=1,
                max_value=10000,
                value=100,
                step=10,
                key=f"volumetry_{endpoint_key}",
                help="Expected number of requests per minute"
            )
        
        with col2:
            expected_concurrent_users = st.number_input(
                "Expected Concurrent Users:",
                min_value=1,
                max_value=1000,
                value=10,
                step=1,
                key=f"users_{endpoint_key}",
                help="Expected number of concurrent users"
            )
        
        # Advanced configuration
        with st.expander("⚙️ Advanced Settings"):
            col1, col2 = st.columns(2)

            with col1:
                timeout_ms = st.number_input(
                    "Timeout (ms):",
                    min_value=1000,
                    max_value=300000,
                    value=30000,
                    step=1000,
                    key=f"timeout_{endpoint_key}",
                    help="Request timeout in milliseconds"
                )

            with col2:
                test_duration = st.number_input(
                    "Test Duration (seconds):",
                    min_value=30,
                    max_value=3600,
                    value=60,
                    step=30,
                    key=f"duration_{endpoint_key}",
                    help="Duration for each test scenario"
                )

        # Scenario explanation (100% target load)
        if expected_volumetry > 0 and expected_concurrent_users > 0:
            st.markdown("---")
            st.markdown("📊 **Configuración del escenario (carga objetivo 100%):**")

            # Calculate metrics
            sleep_time = (expected_concurrent_users * 60) / expected_volumetry if expected_volumetry > 0 else 0
            requests_per_user = expected_volumetry / expected_concurrent_users if expected_concurrent_users > 0 else 0
            total_requests = expected_volumetry  # req/min for 60 seconds = total requests

            info_text = f"""
            • **Duración:** {test_duration} segundos
            • **Usuarios concurrentes:** {expected_concurrent_users}
            • **Volumetría objetivo total:** {expected_volumetry} req/min
            • **Peticiones por usuario:** ~{requests_per_user:.0f} (1 cada {sleep_time:.1f} seg)
            • **Total estimado:** ~{total_requests:.0f} peticiones
            """
            st.markdown(info_text)
            st.markdown("---")

        # Authentication configuration
        auth_config = self._render_auth_configuration(endpoint_key)
        
        # Data configuration
        data_config = self._render_data_configuration(endpoint, endpoint_key)
        
        # Validation
        if expected_volumetry <= 0 or expected_concurrent_users <= 0:
            st.error("Volumetry and concurrent users must be greater than 0")
            return None
        
        # Build endpoint configuration
        endpoint_config = {
            'path': path,
            'method': method,
            'expected_volumetry': expected_volumetry,
            'expected_concurrent_users': expected_concurrent_users,
            'timeout_ms': timeout_ms,
            'test_duration': test_duration,
        }
        
        if auth_config:
            endpoint_config['auth'] = auth_config
        
        if data_config:
            endpoint_config.update(data_config)
        
        return endpoint_config
    
    def _render_auth_configuration(self, endpoint_key: str) -> Optional[Dict]:
        """Render authentication configuration."""
        st.markdown("**🔐 Authentication**")
        
        auth_type = st.selectbox(
            "Authentication Type:",
            options=["none", "bearer_token", "api_key"],
            format_func=lambda x: {
                "none": "No Authentication",
                "bearer_token": "Bearer Token",
                "api_key": "API Key"
            }.get(x, x),
            key=f"auth_type_{endpoint_key}"
        )
        
        if auth_type == "none":
            return None
        
        auth_config = {"type": auth_type}
        
        if auth_type == "bearer_token":
            token = st.text_input(
                "Bearer Token:",
                type="password",
                key=f"token_{endpoint_key}",
                help="Enter the bearer token for authentication"
            )
            if token:
                auth_config["token"] = token
        
        elif auth_type == "api_key":
            col1, col2 = st.columns(2)
            
            with col1:
                api_key = st.text_input(
                    "API Key:",
                    type="password",
                    key=f"api_key_{endpoint_key}",
                    help="Enter the API key"
                )
            
            with col2:
                header_name = st.text_input(
                    "Header Name:",
                    value="X-API-Key",
                    key=f"header_name_{endpoint_key}",
                    help="Header name for the API key"
                )
            
            if api_key:
                auth_config["api_key"] = api_key
                auth_config["header_name"] = header_name
        
        return auth_config if len(auth_config) > 1 else None
    
    def _render_data_configuration(self, endpoint: Dict, endpoint_key: str) -> Dict:
        """Render data configuration options."""
        st.markdown("**📊 Test Data**")
        
        use_mock_data = st.radio(
            "Data Source:",
            options=["mock", "file"],
            format_func=lambda x: {
                "mock": "🤖 Auto-generated (AI Mock Data)",
                "file": "📁 Upload Custom Data File"
            }.get(x, x),
            key=f"data_source_{endpoint_key}",
            help="Choose whether to use AI-generated mock data or upload a custom data file"
        )
        
        config = {"use_mock_data": use_mock_data == "mock"}
        
        if use_mock_data == "file":
            uploaded_file = st.file_uploader(
                "Upload Test Data File:",
                type=['csv', 'json'],
                key=f"data_file_{endpoint_key}",
                help="Upload a CSV or JSON file with test data"
            )
            
            if uploaded_file:
                # Store file info (in real implementation, you'd save the file)
                config["data_file"] = uploaded_file.name
                config["file_size"] = uploaded_file.size
                
                st.success(f"✅ File uploaded: {uploaded_file.name} ({uploaded_file.size} bytes)")
        
        else:
            st.info("🤖 AI will generate realistic mock data based on the OpenAPI schema")
        
        return config