"""
Test Configurator Component
Streamlit component for configuring global test settings
"""

from typing import Dict, List, Optional

import streamlit as st


class TestConfiguratorComponent:
    """Component for configuring global test settings."""
    
    def render(self, selected_endpoints: List[Dict]) -> Optional[Dict]:
        """Render the test configurator component."""
        if not selected_endpoints:
            st.warning("No endpoints selected for configuration.")
            return None
        
        st.markdown("Configure global settings for your load test:")
        
        # Global Authentication
        global_auth = self._render_global_auth()
        
        # Test Settings
        test_settings = self._render_test_settings()
        
        # Degradation Settings
        degradation_settings = self._render_degradation_settings()
        
        # Notification Settings
        notification_settings = self._render_notification_settings()
        
        # Test Name
        test_name = st.text_input(
            "Test Name (Optional):",
            placeholder="My API Load Test",
            help="Give your test a descriptive name"
        )
        
        # Validation and Summary
        if self._validate_configuration(selected_endpoints, global_auth):
            config = {
                'global_auth': global_auth,
                'test_settings': test_settings,
                'degradation_settings': degradation_settings,
                'notification_settings': notification_settings,
                'test_name': test_name or f"LoadTest_{len(selected_endpoints)}_endpoints"
            }
            
            # Add callback URL if provided
            if notification_settings and notification_settings.get('callback_url'):
                config['callback_url'] = notification_settings['callback_url']
            
            self._render_configuration_summary(config, selected_endpoints)
            
            return config
        
        return None
    
    def _render_global_auth(self) -> Optional[Dict]:
        """Render global authentication settings."""
        with st.expander("🔐 Global Authentication", expanded=True):
            st.markdown("Configure authentication that will be applied to all endpoints (unless overridden):")
            
            use_global_auth = st.checkbox(
                "Use global authentication for all endpoints",
                help="If enabled, this authentication will be used for all endpoints that don't have individual auth configured"
            )
            
            if not use_global_auth:
                return None
            
            auth_type = st.selectbox(
                "Global Authentication Type:",
                options=["none", "bearer_token", "api_key"],
                format_func=lambda x: {
                    "none": "No Authentication",
                    "bearer_token": "Bearer Token",
                    "api_key": "API Key"
                }.get(x, x)
            )
            
            if auth_type == "none":
                return None
            
            auth_config = {"type": auth_type}
            
            if auth_type == "bearer_token":
                token = st.text_input(
                    "Global Bearer Token:",
                    type="password",
                    help="This token will be used for all endpoints without individual authentication"
                )
                if token:
                    auth_config["token"] = token
                else:
                    st.warning("Bearer token is required when using bearer token authentication")
                    return None
            
            elif auth_type == "api_key":
                col1, col2 = st.columns(2)
                
                with col1:
                    api_key = st.text_input(
                        "Global API Key:",
                        type="password",
                        help="This API key will be used for all endpoints"
                    )
                
                with col2:
                    header_name = st.text_input(
                        "Header Name:",
                        value="X-API-Key",
                        help="Header name for the API key"
                    )
                
                if api_key:
                    auth_config["api_key"] = api_key
                    auth_config["header_name"] = header_name
                else:
                    st.warning("API key is required when using API key authentication")
                    return None
            
            return auth_config
        
        return None
    
    def _render_test_settings(self) -> Dict:
        """Render general test settings."""
        with st.expander("⚙️ Test Settings", expanded=True):
            col1, col2 = st.columns(2)
            
            with col1:
                default_duration = st.number_input(
                    "Default Test Duration (seconds):",
                    min_value=30,
                    max_value=3600,
                    value=60,
                    step=30,
                    help="Default duration for each test scenario"
                )
                
                ramp_up_time = st.number_input(
                    "Ramp-up Time (seconds):",
                    min_value=5,
                    max_value=300,
                    value=10,
                    step=5,
                    help="Time to gradually increase load to target level"
                )
            
            with col2:
                think_time = st.number_input(
                    "Think Time (seconds):",
                    min_value=0.1,
                    max_value=10.0,
                    value=1.0,
                    step=0.1,
                    help="Delay between requests to simulate real user behavior"
                )
                
                ramp_down_time = st.number_input(
                    "Ramp-down Time (seconds):",
                    min_value=5,
                    max_value=300,
                    value=10,
                    step=5,
                    help="Time to gradually decrease load to zero"
                )
            
            return {
                'default_duration': default_duration,
                'ramp_up_time': ramp_up_time,
                'ramp_down_time': ramp_down_time,
                'think_time': think_time
            }
    
    def _render_degradation_settings(self) -> Dict:
        """Render degradation detection settings."""
        with st.expander("📉 Degradation Detection", expanded=False):
            st.markdown("Configure when to stop the test due to performance degradation:")
            
            col1, col2 = st.columns(2)
            
            with col1:
                response_time_multiplier = st.number_input(
                    "Response Time Threshold (multiplier):",
                    min_value=1.5,
                    max_value=10.0,
                    value=5.0,
                    step=0.5,
                    help="Stop test when response time exceeds baseline × this multiplier"
                )
                
                initial_user_percentage = st.number_input(
                    "Initial User Percentage:",
                    min_value=0.05,
                    max_value=0.5,
                    value=0.1,
                    step=0.05,
                    help="Start test with this percentage of expected users"
                )
            
            with col2:
                error_rate_threshold = st.number_input(
                    "Error Rate Threshold (%):",
                    min_value=5,
                    max_value=95,
                    value=50,
                    step=5,
                    help="Stop test when error rate exceeds this percentage"
                )
                
                user_increment_percentage = st.number_input(
                    "User Increment Percentage:",
                    min_value=0.1,
                    max_value=2.0,
                    value=0.5,
                    step=0.1,
                    help="Increase users by this percentage in each scenario"
                )
            
            stop_error_threshold = st.number_input(
                "Critical Stop Threshold (%):",
                min_value=50,
                max_value=100,
                value=60,
                step=5,
                help="Immediately stop test when error rate reaches this level"
            )
            
            return {
                'response_time_multiplier': response_time_multiplier,
                'error_rate_threshold': error_rate_threshold / 100,  # Convert to decimal
                'initial_user_percentage': initial_user_percentage,
                'user_increment_percentage': user_increment_percentage,
                'stop_error_threshold': stop_error_threshold / 100  # Convert to decimal
            }
    
    def _render_notification_settings(self) -> Optional[Dict]:
        """Render notification settings."""
        with st.expander("🔔 Notifications", expanded=False):
            st.markdown("Configure notifications for test completion:")
            
            enable_callback = st.checkbox(
                "Enable callback notification",
                help="Receive a HTTP callback when the test completes"
            )
            
            if not enable_callback:
                return None
            
            callback_url = st.text_input(
                "Callback URL:",
                placeholder="https://your-api.com/webhook/loadtest-complete",
                help="URL that will receive a POST request when the test completes"
            )
            
            if callback_url:
                # Validate URL format
                if not callback_url.startswith(('http://', 'https://')):
                    st.error("Callback URL must start with http:// or https://")
                    return None
                
                return {
                    'callback_url': callback_url,
                    'enabled': True
                }
            else:
                st.warning("Please provide a callback URL")
                return None
        
        return None
    
    def _validate_configuration(self, selected_endpoints: List[Dict], global_auth: Optional[Dict]) -> bool:
        """Validate the test configuration."""
        validation_errors = []
        
        # Check if endpoints are properly configured
        for endpoint in selected_endpoints:
            if not endpoint.get('expected_volumetry') or endpoint.get('expected_volumetry') <= 0:
                validation_errors.append(f"Invalid volumetry for {endpoint.get('method')} {endpoint.get('path')}")
            
            if not endpoint.get('expected_concurrent_users') or endpoint.get('expected_concurrent_users') <= 0:
                validation_errors.append(f"Invalid concurrent users for {endpoint.get('method')} {endpoint.get('path')}")
        
        # Check authentication
        endpoints_without_auth = [
            ep for ep in selected_endpoints 
            if not ep.get('auth') and not global_auth
        ]
        
        if endpoints_without_auth and not global_auth:
            st.info(f"ℹ️ {len(endpoints_without_auth)} endpoint(s) will run without authentication")
        
        if validation_errors:
            st.error("Configuration validation failed:")
            for error in validation_errors:
                st.error(f"• {error}")
            return False
        
        return True
    
    def _render_configuration_summary(self, config: Dict, selected_endpoints: List[Dict]):
        """Render a summary of the configuration."""
        st.markdown("---")
        st.markdown("### 📋 Configuration Summary")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Selected Endpoints", len(selected_endpoints))
            total_users = sum(ep.get('expected_concurrent_users', 0) for ep in selected_endpoints)
            st.metric("Total Expected Users", total_users)
        
        with col2:
            total_volumetry = sum(ep.get('expected_volumetry', 0) for ep in selected_endpoints)
            st.metric("Total Expected Req/Min", total_volumetry)
            
            auth_type = "None"
            if config.get('global_auth'):
                auth_type = config['global_auth'].get('type', 'Unknown').title()
            st.metric("Global Authentication", auth_type)
        
        with col3:
            duration = config.get('test_settings', {}).get('default_duration', 60)
            st.metric("Test Duration", f"{duration}s")
            
            callback_enabled = bool(config.get('callback_url'))
            st.metric("Notifications", "Enabled" if callback_enabled else "Disabled")
        
        # Advanced settings summary
        with st.expander("📊 Detailed Settings"):
            st.json(config)