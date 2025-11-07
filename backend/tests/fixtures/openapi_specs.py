"""
OpenAPI Specification Fixtures
Sample OpenAPI specs for testing
"""

import json

# ============================================================================
# VALID OPENAPI 3.0 JSON
# ============================================================================

VALID_OPENAPI_JSON = json.dumps({
    "openapi": "3.0.0",
    "info": {
        "title": "Test API",
        "description": "A test API for unit testing",
        "version": "1.0.0"
    },
    "servers": [
        {
            "url": "https://api.test.example.com/v1"
        }
    ],
    "paths": {
        "/users": {
            "get": {
                "summary": "List users",
                "description": "Get a list of all users",
                "parameters": [
                    {
                        "name": "page",
                        "in": "query",
                        "schema": {"type": "integer", "default": 1}
                    },
                    {
                        "name": "limit",
                        "in": "query",
                        "schema": {"type": "integer", "default": 10}
                    }
                ],
                "responses": {
                    "200": {
                        "description": "Successful response"
                    }
                }
            },
            "post": {
                "summary": "Create user",
                "description": "Create a new user",
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "required": ["name", "email"],
                                "properties": {
                                    "name": {"type": "string"},
                                    "email": {"type": "string", "format": "email"},
                                    "age": {"type": "integer", "minimum": 0}
                                }
                            }
                        }
                    }
                },
                "responses": {
                    "201": {
                        "description": "User created"
                    }
                }
            }
        },
        "/users/{userId}": {
            "get": {
                "summary": "Get user by ID",
                "description": "Retrieve a single user",
                "parameters": [
                    {
                        "name": "userId",
                        "in": "path",
                        "required": True,
                        "schema": {"type": "integer"}
                    }
                ],
                "responses": {
                    "200": {
                        "description": "Successful response"
                    },
                    "404": {
                        "description": "User not found"
                    }
                }
            }
        }
    }
})


# ============================================================================
# VALID OPENAPI 3.0 YAML
# ============================================================================

VALID_OPENAPI_YAML = """
openapi: 3.0.0
info:
  title: Test API YAML
  description: A test API in YAML format
  version: 1.0.0
servers:
  - url: https://api.test.example.com/v1
paths:
  /products:
    get:
      summary: List products
      parameters:
        - name: category
          in: query
          schema:
            type: string
      responses:
        '200':
          description: Successful response
    post:
      summary: Create product
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required:
                - name
                - price
              properties:
                name:
                  type: string
                price:
                  type: number
                  minimum: 0
      responses:
        '201':
          description: Product created
"""


# ============================================================================
# PETSTORE API (COMMON TEST EXAMPLE)
# ============================================================================

PETSTORE_OPENAPI_SPEC = json.dumps({
    "openapi": "3.0.0",
    "info": {
        "title": "Swagger Petstore",
        "description": "This is a sample Pet Store Server based on the OpenAPI 3.0 specification.",
        "version": "1.0.0"
    },
    "servers": [
        {
            "url": "https://petstore3.swagger.io/api/v3"
        }
    ],
    "paths": {
        "/pet": {
            "post": {
                "summary": "Add a new pet to the store",
                "operationId": "addPet",
                "requestBody": {
                    "description": "Create a new pet in the store",
                    "content": {
                        "application/json": {
                            "schema": {
                                "$ref": "#/components/schemas/Pet"
                            }
                        }
                    },
                    "required": True
                },
                "responses": {
                    "200": {
                        "description": "Successful operation"
                    }
                }
            }
        },
        "/pet/{petId}": {
            "get": {
                "summary": "Find pet by ID",
                "operationId": "getPetById",
                "parameters": [
                    {
                        "name": "petId",
                        "in": "path",
                        "required": True,
                        "schema": {
                            "type": "integer",
                            "format": "int64"
                        }
                    }
                ],
                "responses": {
                    "200": {
                        "description": "successful operation"
                    },
                    "404": {
                        "description": "Pet not found"
                    }
                }
            }
        }
    },
    "components": {
        "schemas": {
            "Pet": {
                "type": "object",
                "required": ["name", "photoUrls"],
                "properties": {
                    "id": {
                        "type": "integer",
                        "format": "int64"
                    },
                    "name": {
                        "type": "string",
                        "example": "doggie"
                    },
                    "category": {
                        "$ref": "#/components/schemas/Category"
                    },
                    "photoUrls": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "format": "uri"
                        }
                    },
                    "tags": {
                        "type": "array",
                        "items": {
                            "$ref": "#/components/schemas/Tag"
                        }
                    },
                    "status": {
                        "type": "string",
                        "description": "pet status in the store",
                        "enum": ["available", "pending", "sold"]
                    }
                }
            },
            "Category": {
                "type": "object",
                "properties": {
                    "id": {
                        "type": "integer",
                        "format": "int64"
                    },
                    "name": {
                        "type": "string"
                    }
                }
            },
            "Tag": {
                "type": "object",
                "properties": {
                    "id": {
                        "type": "integer",
                        "format": "int64"
                    },
                    "name": {
                        "type": "string"
                    }
                }
            }
        }
    }
})


# ============================================================================
# INVALID OPENAPI SPECS (FOR ERROR TESTING)
# ============================================================================

INVALID_OPENAPI_MISSING_INFO = json.dumps({
    "openapi": "3.0.0",
    "paths": {}
})

INVALID_OPENAPI_MISSING_VERSION = json.dumps({
    "info": {
        "title": "Test API"
    },
    "paths": {}
})

INVALID_OPENAPI_WRONG_FORMAT = "This is not JSON or YAML"

INVALID_JSON_SYNTAX = '{"openapi": "3.0.0", "info": {'


# ============================================================================
# OPENAPI WITH COMPLEX REFS
# ============================================================================

COMPLEX_OPENAPI_WITH_REFS = json.dumps({
    "openapi": "3.0.0",
    "info": {
        "title": "Complex API with Refs",
        "version": "1.0.0"
    },
    "servers": [
        {"url": "https://api.complex.example.com"}
    ],
    "paths": {
        "/orders": {
            "post": {
                "summary": "Create order",
                "requestBody": {
                    "content": {
                        "application/json": {
                            "schema": {
                                "$ref": "#/components/schemas/Order"
                            }
                        }
                    }
                },
                "responses": {
                    "201": {
                        "description": "Order created"
                    }
                }
            }
        }
    },
    "components": {
        "schemas": {
            "Order": {
                "type": "object",
                "required": ["customer", "items"],
                "properties": {
                    "id": {"type": "integer"},
                    "customer": {
                        "$ref": "#/components/schemas/Customer"
                    },
                    "items": {
                        "type": "array",
                        "items": {
                            "$ref": "#/components/schemas/OrderItem"
                        }
                    }
                }
            },
            "Customer": {
                "type": "object",
                "required": ["name", "email"],
                "properties": {
                    "id": {"type": "integer"},
                    "name": {"type": "string"},
                    "email": {"type": "string", "format": "email"},
                    "address": {
                        "$ref": "#/components/schemas/Address"
                    }
                }
            },
            "Address": {
                "type": "object",
                "properties": {
                    "street": {"type": "string"},
                    "city": {"type": "string"},
                    "zipCode": {"type": "string"}
                }
            },
            "OrderItem": {
                "type": "object",
                "required": ["productId", "quantity"],
                "properties": {
                    "productId": {"type": "integer"},
                    "quantity": {"type": "integer", "minimum": 1},
                    "price": {"type": "number"}
                }
            }
        }
    }
})


# ============================================================================
# OPENAPI WITH BOM (BYTE ORDER MARK)
# ============================================================================

OPENAPI_WITH_BOM = '\ufeff' + VALID_OPENAPI_JSON


# ============================================================================
# MINIMAL VALID OPENAPI
# ============================================================================

MINIMAL_VALID_OPENAPI = json.dumps({
    "openapi": "3.0.0",
    "info": {
        "title": "Minimal API",
        "version": "1.0.0"
    },
    "paths": {}
})


# ============================================================================
# OPENAPI 2.0 (SWAGGER)
# ============================================================================

SWAGGER_2_0_SPEC = json.dumps({
    "swagger": "2.0",
    "info": {
        "title": "Swagger 2.0 API",
        "version": "1.0.0"
    },
    "host": "api.example.com",
    "basePath": "/v1",
    "schemes": ["https"],
    "paths": {
        "/items": {
            "get": {
                "summary": "List items",
                "responses": {
                    "200": {
                        "description": "Successful response"
                    }
                }
            }
        }
    }
})
