#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Script to test load test creation with PetStore API"""

import json
import requests
import time
import sys

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Read OpenAPI spec
print(">> Leyendo OpenAPI spec...")
with open('G:/Mi unidad/PSU-IA/Q2/TF1/src/mocked-test-api/openapi.json', 'r') as f:
    spec_content = f.read()

# Create load test request
load_test_request = {
    "api_spec": spec_content,
    "selected_endpoints": [
        {
            "path": "/pet",
            "method": "POST",
            "expected_volumetry": 100,
            "expected_concurrent_users": 10,
            "timeout_ms": 30000,
            "use_mock_data": True
        }
    ],
    "test_name": "PetStore POST /pet Load Test - Schema Fix Test"
}

# Send request to backend
print(">> Creando prueba de carga...")
response = requests.post(
    "http://localhost:8000/api/v1/load-test",
    json=load_test_request,
    headers={"Content-Type": "application/json"},
    timeout=30
)

print(f"\n>> Status Code: {response.status_code}")

if response.status_code == 202:
    result = response.json()
    job_id = result['job_id']
    print(f">> Job creado exitosamente!")
    print(f"   Job ID: {job_id}")
    print(f"   Status: {result['status']}")
    print(f"   Status URL: {result['status_url']}")

    # Monitor job progress
    print(f"\n>> Monitoreando progreso del job...")

    for i in range(60):  # Check for up to 5 minutes
        time.sleep(5)
        status_response = requests.get(f"http://localhost:8000/api/v1/status/{job_id}")

        if status_response.status_code == 200:
            status_data = status_response.json()
            progress = status_data.get('progress', 0)
            job_status = status_data.get('status', 'UNKNOWN')

            print(f"   [{i*5}s] Status: {job_status} | Progress: {progress:.1f}%")

            if job_status == "FINISHED":
                print(f"\n>> Test completado!")
                print(f"   Report URL: {status_data.get('report_url', 'N/A')}")
                break
            elif job_status == "FAILED":
                print(f"\n>> Test fallo!")
                break

    # Save job_id
    with open('G:/Mi unidad/PSU-IA/Q2/TF1/src/last_job_id.txt', 'w') as f:
        f.write(job_id)
    print(f"\n>> Job ID guardado en: last_job_id.txt")

else:
    print(f">> Error creando job:")
    print(f"   {response.text}")
