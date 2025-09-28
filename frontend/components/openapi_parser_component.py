"""
OpenAPI Parser Component
Streamlit component for loading and parsing OpenAPI specifications
"""

import json
from typing import Dict, List, Optional

import requests
import streamlit as st
import validators
import yaml


class OpenAPIParserComponent:
    """Component for parsing OpenAPI specifications."""
    
    def __init__(self, backend_url: str):
        self.backend_url = backend_url
    
    def render(self) -> Optional[Dict]:
        """Render the OpenAPI parser component."""
        st.markdown("Load your OpenAPI specification to begin testing.")

        # Input method selection
        input_method = st.radio(
            "How would you like to provide your OpenAPI specification?",
            ["📄 Paste Content", "🌐 URL", "📁 Upload File"],
            horizontal=True
        )

        spec_content = None

        if input_method == "📄 Paste Content":
            spec_content = self._render_text_input()
        elif input_method == "🌐 URL":
            spec_content = self._render_url_input()
        elif input_method == "📁 Upload File":
            spec_content = self._render_file_upload()

        if spec_content:
            # Store the spec content in session state for persistence
            st.session_state.temp_spec_content = spec_content
            return self._process_specification(spec_content)

        # Check if we have a pending validation from session state
        if hasattr(st.session_state, 'temp_spec_content') and st.session_state.temp_spec_content:
            return self._process_specification(st.session_state.temp_spec_content)

        return None
    
    def _render_text_input(self) -> Optional[str]:
        """Render text area for pasting OpenAPI content."""
        spec_content = st.text_area(
            "Paste your OpenAPI specification (JSON or YAML):",
            height=300,
            placeholder="Paste your OpenAPI 3.0+ specification here...",
            help="You can paste JSON or YAML format OpenAPI specifications"
        )
        
        if spec_content and spec_content.strip():
            return spec_content.strip()
        
        return None
    
    def _render_url_input(self) -> Optional[str]:
        """Render URL input for fetching OpenAPI specification."""
        url = st.text_input(
            "Enter OpenAPI specification URL:",
            placeholder="https://api.example.com/openapi.json",
            help="URL should return a valid OpenAPI 3.0+ specification"
        )
        
        if url and url.strip():
            if validators.url(url):
                if st.button("🔄 Fetch Specification", type="secondary"):
                    return self._fetch_from_url(url)
            else:
                st.error("Please enter a valid URL")
        
        return None
    
    def _render_file_upload(self) -> Optional[str]:
        """Render file upload for OpenAPI specification."""
        uploaded_file = st.file_uploader(
            "Upload OpenAPI specification file:",
            type=['json', 'yaml', 'yml'],
            help="Upload a JSON or YAML file containing your OpenAPI specification"
        )
        
        if uploaded_file is not None:
            try:
                content = uploaded_file.read().decode('utf-8')
                return content
            except Exception as e:
                st.error(f"Error reading file: {str(e)}")
        
        return None
    
    def _fetch_from_url(self, url: str) -> Optional[str]:
        """Fetch OpenAPI specification from URL."""
        try:
            with st.spinner(f"Fetching specification from {url}..."):
                response = requests.get(url, timeout=30)
                response.raise_for_status()
                
                # Try to parse as JSON first, then YAML
                try:
                    json.loads(response.text)
                    return response.text
                except json.JSONDecodeError:
                    try:
                        yaml.safe_load(response.text)
                        return response.text
                    except yaml.YAMLError:
                        st.error("URL does not return valid JSON or YAML content")
                        return None
        
        except requests.exceptions.RequestException as e:
            st.error(f"Error fetching from URL: {str(e)}")
            return None
    
    def _process_specification(self, spec_content: str) -> Optional[Dict]:
        """Process and validate the OpenAPI specification."""
        try:
            # First, try to parse locally to give immediate feedback
            local_parsed = self._parse_spec_locally(spec_content)
            
            if not local_parsed:
                return None
            
            # Show basic info
            with st.expander("📋 Specification Preview", expanded=True):
                info = local_parsed.get('info', {})
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.write(f"**Title:** {info.get('title', 'N/A')}")
                with col2:
                    st.write(f"**Version:** {info.get('version', 'N/A')}")
                with col3:
                    paths_count = len(local_parsed.get('paths', {}))
                    st.write(f"**Paths:** {paths_count}")
                
                if info.get('description'):
                    st.write(f"**Description:** {info['description']}")
            
            # Validate with backend
            if st.button("✅ Validate & Parse Specification", type="primary"):
                result = self._validate_with_backend(spec_content, local_parsed)
                if result and result.get('success'):
                    # Store all the result data in session state before rerun
                    st.session_state.openapi_spec = result['spec_content']
                    st.session_state.parsed_spec = result['parsed_spec']
                    st.session_state.available_endpoints = result['endpoints']
                    st.session_state.validated_spec = True

                    # Clear temp content
                    if hasattr(st.session_state, 'temp_spec_content'):
                        del st.session_state.temp_spec_content

                    st.rerun()
                return result
        
        except Exception as e:
            st.error(f"Error processing specification: {str(e)}")
        
        return None
    
    def _parse_spec_locally(self, spec_content: str) -> Optional[Dict]:
        """Parse specification locally for preview."""
        try:
            # Try JSON first
            try:
                return json.loads(spec_content)
            except json.JSONDecodeError:
                # Try YAML
                return yaml.safe_load(spec_content)
        
        except Exception as e:
            st.error(f"Invalid JSON/YAML format: {str(e)}")
            return None
    
    def _validate_with_backend(self, spec_content: str, local_parsed: Dict) -> Optional[Dict]:
        """Validate specification with backend and get parsed endpoints."""
        try:
            with st.spinner("Validating specification with backend..."):
                # Validate specification
                validate_response = requests.post(
                    f"{self.backend_url}/api/v1/openapi/validate",
                    json={"spec_content": spec_content},
                    timeout=30
                )
                
                if validate_response.status_code != 200:
                    st.error(f"Validation failed: {validate_response.text}")
                    return None
                
                validation_result = validate_response.json()
                
                if not validation_result.get('valid', False):
                    st.error(f"Invalid OpenAPI specification: {validation_result.get('message', 'Unknown error')}")
                    if validation_result.get('errors'):
                        for error in validation_result['errors']:
                            st.error(f"- {error}")
                    return None
                
                st.success("✅ Specification is valid!")
                
                # Extract endpoints from local parsing as fallback
                endpoints = self._extract_endpoints_locally(local_parsed)

                # Try backend parsing first, but fallback to local if it fails
                try:
                    parse_response = requests.post(
                        f"{self.backend_url}/api/v1/openapi/parse",
                        json={"spec_content": spec_content},
                        timeout=30
                    )

                    if parse_response.status_code == 200:
                        parse_result = parse_response.json()
                        endpoints = parse_result.get('endpoints', endpoints)  # Use backend result if available
                        st.success("✅ Specification parsed successfully!")
                    else:
                        st.warning("Backend parsing failed, using local extraction")

                except Exception as parse_error:
                    st.warning(f"Backend parsing failed ({str(parse_error)}), using local extraction")

                return {
                    'success': True,
                    'spec_content': spec_content,
                    'parsed_spec': local_parsed,
                    'endpoints': endpoints,
                    'total_endpoints': len(endpoints)
                }
        
        except Exception as e:
            st.error(f"Error validating with backend: {str(e)}")
            return None

    def _extract_endpoints_locally(self, parsed_spec: Dict) -> List[Dict]:
        """Extract endpoints from locally parsed OpenAPI spec."""
        endpoints = []
        paths = parsed_spec.get('paths', {})

        for path, path_data in paths.items():
            for method, operation in path_data.items():
                if method.upper() in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS']:
                    endpoint = {
                        'path': path,
                        'method': method.upper(),
                        'summary': operation.get('summary', ''),
                        'description': operation.get('description', ''),
                        'parameters': operation.get('parameters', []),
                        'request_body': operation.get('requestBody', {}),
                        'responses': operation.get('responses', {})
                    }
                    endpoints.append(endpoint)

        return endpoints