# Mocked Test API (Static OpenAPI Spec)

This service mocks the Petstore OpenAPI v3 specification using Stoplight Prism.
The OpenAPI spec (`openapi.json`) is included statically inside the container.

## How it works
- Starts a Prism mock server on port 4010 using the included `openapi.json`.
- Runs a lightweight Express proxy on port 8000 that:
  - Serves `/health` endpoint (returns `{ "status": "ok" }`).
  - Proxies all other requests to Prism mock.

## Usage
```bash
docker build -t mocked-test-api ./mocked_test_api
docker run -p 8000:8000 mocked-test-api
```

The service will be available at `http://localhost:8000`.
