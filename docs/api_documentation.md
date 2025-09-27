# LoadTester API Documentation

## Overview

LoadTester provides a RESTful API for creating and managing automated load tests based on OpenAPI specifications. The API follows REST principles and returns JSON responses.

## Base URL

```
http://localhost:8000/api/v1
```

## Authentication

The LoadTester API currently does not require authentication for access. All endpoints are publicly accessible.

## API Endpoints

### Load Testing

#### Create Load Test

Creates a new load test job based on an OpenAPI specification.

**Endpoint:** `POST /load-test`

**Request Body:**
```json
{
  "api_spec": "string",
  "selected_endpoints": [
    {
      "path": "/users/{id}",
      "method": "GET",
      "expected_volumetry": 100,
      "expected_concurrent_users": 10,
      "timeout_ms": 30000,
      "auth": {
        "auth_type": "bearer_token",
        "token": "eyJhbGciOiJIUzI1NiIs..."
      },
      "use_mock_data": true
    }
  ],
  "global_auth": {
    "auth_type": "api_key",
    "api_key": "sk-1234567890",
    "header_name": "X-API-Key"
  },
  "callback_url": "https://your-app.com/webhook",
  "test_name": "My API Load Test"
}
```

**Response:** `202 Accepted`
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "PENDING",
  "status_url": "/api/v1/status/550e8400-e29b-41d4-a716-446655440000",
  "message": "Load test job created and started"
}
```

**Possible Error Responses:**
- `400 Bad Request` - Invalid configuration
- `409 Conflict` - Maximum concurrent jobs reached
- `500 Internal Server Error` - Server error

---

### Job Status

#### Get Job Status

Retrieves the current status and progress of a load test job.

**Endpoint:** `GET /status/{job_id}`

**Response:** `200 OK`
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "RUNNING",
  "progress": 45.2,
  "created_at": "2024-01-15T10:30:00Z",
  "started_at": "2024-01-15T10:30:05Z",
  "finished_at": null,
  "report_url": null
}
```

**Status Values:**
- `PENDING` - Job created but not started
- `RUNNING` - Job currently executing
- `FINISHED` - Job completed successfully
- `FAILED` - Job failed with errors

**For completed jobs:**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "FINISHED",
  "progress": 100.0,
  "created_at": "2024-01-15T10:30:00Z",
  "started_at": "2024-01-15T10:30:05Z",
  "finished_at": "2024-01-15T10:35:22Z",
  "report_url": "/api/v1/report/550e8400-e29b-41d4-a716-446655440000"
}
```

**Possible Error Responses:**
- `404 Not Found` - Job not found

---

### Reports

#### Download Report

Downloads the PDF report for a completed load test.

**Endpoint:** `GET /report/{job_id}`

**Response:** `200 OK`
- Content-Type: `application/pdf`
- Content-Disposition: `attachment; filename=loadtest_report_{job_id}.pdf`

**Possible Error Responses:**
- `400 Bad Request` - Report not available (job not finished)
- `404 Not Found` - Job or report not found

#### List Reports

Gets a list of all available reports.

**Endpoint:** `GET /reports`

**Response:** `200 OK`
```json
{
  "reports": [
    {
      "job_id": "550e8400-e29b-41d4-a716-446655440000",
      "filename": "loadtest_report_550e8400-e29b-41d4-a716-446655440000.pdf",
      "size": 2048576,
      "created_at": 1705312200,
      "download_url": "/api/v1/report/550e8400-e29b-41d4-a716-446655440000"
    }
  ],
  "total": 1
}
```

#### Get Report Info

Gets information about a report without downloading it.

**Endpoint:** `GET /report/{job_id}/info`

**Response:** `200 OK`
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "filename": "loadtest_report_550e8400-e29b-41d4-a716-446655440000.pdf",
  "size": 2048576,
  "created_at": 1705312200,
  "job_status": "FINISHED",
  "job_created_at": "2024-01-15T10:30:00Z",
  "job_finished_at": "2024-01-15T10:35:22Z",
  "download_url": "/api/v1/report/550e8400-e29b-41d4-a716-446655440000"
}
```

#### Delete Report

Deletes a report file.

**Endpoint:** `DELETE /report/{job_id}`

**Response:** `200 OK`
```json
{
  "message": "Report 550e8400-e29b-41d4-a716-446655440000 deleted successfully",
  "job_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

---

### OpenAPI Specification

#### Validate Specification

Validates an OpenAPI specification format.

**Endpoint:** `POST /openapi/validate`

**Request Body:**
```json
{
  "spec_content": "... OpenAPI JSON/YAML content ..."
}
```

**Response:** `200 OK`
```json
{
  "valid": true,
  "message": "OpenAPI specification is valid",
  "errors": []
}
```

**For invalid specifications:**
```json
{
  "valid": false,
  "message": "OpenAPI specification is invalid",
  "errors": [
    "Missing required field: info.title",
    "Invalid OpenAPI version"
  ]
}
```

#### Parse Specification

Parses an OpenAPI specification and extracts endpoint information.

**Endpoint:** `POST /openapi/parse`

**Request Body:**
```json
{
  "spec_content": "... OpenAPI JSON/YAML content ..."
}
```

**Response:** `200 OK`
```json
{
  "info": {
    "title": "Pet Store API",
    "description": "A sample API",
    "version": "1.0.0"
  },
  "servers": [
    {
      "url": "https://petstore.swagger.io/v2"
    }
  ],
  "endpoints": [
    {
      "path": "/pet/{petId}",
      "method": "GET",
      "summary": "Find pet by ID",
      "description": "Returns a single pet",
      "parameters": [
        {
          "name": "petId",
          "in": "path",
          "required": true,
          "schema": {
            "type": "integer"
          }
        }
      ],
      "responses": {
        "200": {
          "description": "successful operation"
        }
      }
    }
  ],
  "total_endpoints": 1
}
```

#### Filter Endpoints

Filters endpoints by method, path pattern, or other criteria.

**Endpoint:** `POST /openapi/endpoints/filter`

**Request Body:**
```json
{
  "spec_content": "... OpenAPI content ...",
  "methods": ["GET", "POST"],
  "path_pattern": "/users"
}
```

**Response:** `200 OK`
```json
{
  "total_available": 15,
  "total_filtered": 3,
  "endpoints": [
    {
      "path": "/users",
      "method": "GET",
      "summary": "List users"
    },
    {
      "path": "/users",
      "method": "POST", 
      "summary": "Create user"
    },
    {
      "path": "/users/{id}",
      "method": "GET",
      "summary": "Get user by ID"
    }
  ],
  "filters_applied": {
    "methods": ["GET", "POST"],
    "path_pattern": "/users"
  }
}
```

---

### System

#### Health Check

Checks the health of the LoadTester service.

**Endpoint:** `GET /health`

**Response:** `200 OK`
```json
{
  "status": "healthy",
  "service": "LoadTester",
  "version": "0.0.1",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

#### System Information

Gets system information and configuration.

**Endpoint:** `GET /system/info`

**Response:** `200 OK`
```json
{
  "service": {
    "name": "LoadTester",
    "version": "0.0.1",
    "debug": false
  },
  "configuration": {
    "max_concurrent_jobs": 1,
    "max_file_size": 10485760,
    "default_test_duration": 60,
    "degradation_settings": {
      "response_time_multiplier": 5.0,
      "error_rate_threshold": 0.5,
      "initial_user_percentage": 0.1,
      "user_increment_percentage": 0.5,
      "stop_error_threshold": 0.6
    }
  },
  "features": {
    "ai_services_available": true,
    "supported_file_types": [".csv", ".json", ".xlsx"]
  }
}
```

#### System Metrics

Gets basic system metrics.

**Endpoint:** `GET /metrics`

**Response:** `200 OK`
```json
{
  "jobs": {
    "total": 25,
    "pending": 0,
    "running": 1,
    "finished": 22,
    "failed": 2
  },
  "tests": {
    "total_executions": 156,
    "total_scenarios": 89,
    "avg_execution_time": 142.5
  },
  "system": {
    "uptime": "2h 15m 32s",
    "memory_usage": "245 MB",
    "disk_usage": "1.2 GB"
  }
}
```

---

## Error Handling

All API endpoints return structured error responses in the following format:

```json
{
  "error": {
    "type": "error_type",
    "message": "Human-readable error message",
    "details": {
      "field_name": "additional_context"
    }
  }
}
```

### Common Error Types

- `validation_error` - Input validation failed
- `invalid_configuration` - Load test configuration is invalid
- `resource_not_found` - Requested resource not found
- `execution_error` - Error during test execution
- `external_service_error` - External service (AI, K6) error
- `internal_server_error` - Unexpected server error

### HTTP Status Codes

- `200 OK` - Request successful
- `202 Accepted` - Request accepted (async operation)
- `400 Bad Request` - Invalid request data
- `404 Not Found` - Resource not found
- `409 Conflict` - Resource conflict (e.g., max jobs reached)
- `422 Unprocessable Entity` - Validation error
- `500 Internal Server Error` - Server error
- `502 Bad Gateway` - External service error

---

## Rate Limiting

Currently, LoadTester does not implement rate limiting. However, the following limits apply:

- **Concurrent Jobs**: Maximum 1 concurrent load test (configurable)
- **File Size**: Maximum 10MB for uploaded data files
- **Request Timeout**: 30 seconds for API calls
- **Test Duration**: Configurable per endpoint (default 60 seconds)

---

## Webhooks / Callbacks

When creating a load test with a `callback_url`, LoadTester will send a POST request to that URL when the test completes:

**Callback Request:**
```http
POST https://your-app.com/webhook
Content-Type: application/json

{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "FINISHED",
  "completed_at": "2024-01-15T10:35:22Z",
  "report_url": "http://loadtester.example.com/api/v1/report/550e8400-e29b-41d4-a716-446655440000"
}
```

**Callback Retry Policy:**
- Maximum 3 retry attempts
- 30-second timeout per attempt
- No retry for 4xx client errors

---

## Examples

### Complete Load Test Flow

```bash
# 1. Create a load test
curl -X POST "http://localhost:8000/api/v1/load-test" \
  -H "Content-Type: application/json" \
  -d '{
    "api_spec": "... OpenAPI spec ...",
    "selected_endpoints": [
      {
        "path": "/users/{id}",
        "method": "GET", 
        "expected_volumetry": 100,
        "expected_concurrent_users": 10
      }
    ]
  }'

# Response: {"job_id": "550e8400-...", "status": "PENDING", ...}

# 2. Check status
curl "http://localhost:8000/api/v1/status/550e8400-e29b-41d4-a716-446655440000"

# 3. Download report when finished
curl "http://localhost:8000/api/v1/report/550e8400-e29b-41d4-a716-446655440000" \
  --output loadtest_report.pdf
```

For more examples and interactive documentation, visit the OpenAPI documentation at `/docs` when the service is running.