"""Test script to verify demo-test-api endpoint and schema."""
import requests
import json

# Test the OpenAPI schema
print("Fetching OpenAPI schema...")
response = requests.get("http://localhost:8020/openapi.json")
if response.status_code == 200:
    openapi = response.json()
    print(f"\nAPI Title: {openapi.get('info', {}).get('title')}")
    print(f"Servers: {openapi.get('servers', [])}")

    # Check POST /alumnos schema
    post_alumnos = openapi.get('paths', {}).get('/alumnos', {}).get('post', {})
    if post_alumnos:
        print("\n\nPOST /alumnos schema:")
        request_body = post_alumnos.get('requestBody', {})
        print(json.dumps(request_body, indent=2))
else:
    print(f"Failed to fetch OpenAPI schema: {response.status_code}")

# Test the endpoint with valid data
print("\n\nTesting POST /alumnos with valid data...")
test_data = {
    "nombre": "Juan",
    "apellido": "Pérez",
    "edad": 22,
    "email": "juan.perez@example.com",
    "carrera": "Ingeniería Informática"
}

response = requests.post(
    "http://localhost:8020/alumnos",
    json=test_data,
    headers={"Content-Type": "application/json"}
)

print(f"Status Code: {response.status_code}")
print(f"Response: {json.dumps(response.json(), indent=2)}")
