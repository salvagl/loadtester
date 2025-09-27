# LoadTester Data Formats

## Overview

LoadTester supports multiple data formats for providing test data to your load tests. You can either let the AI generate realistic mock data automatically or provide your own custom data files.

## Data Sources

### 1. AI-Generated Mock Data (Recommended)

LoadTester can automatically generate realistic test data based on your OpenAPI specification using AI services.

**Advantages:**
- No file preparation required
- Automatically respects OpenAPI schema constraints
- Generates realistic data types (emails, names, dates, etc.)
- Handles complex data relationships

**Generated Data Types:**
- **Strings**: Names, addresses, descriptions, UUIDs
- **Numbers**: Integers, floats with realistic ranges
- **Dates**: ISO 8601 formatted dates and datetimes
- **Emails**: Valid email addresses
- **Phone Numbers**: Formatted phone numbers
- **URLs**: Valid URLs and URIs
- **Booleans**: Random true/false values

**Example Generated Data:**
```json
{
  "path_params": {
    "id": 1247,
    "userId": 5892
  },
  "query_params": {
    "page": 3,
    "limit": 25,
    "filter": "active"
  },
  "body": {
    "name": "John Smith",
    "email": "john.smith@example.com",
    "phone": "+1-555-123-4567",
    "address": "123 Main St, Springfield, IL 62701",
    "birthDate": "1985-03-15",
    "isActive": true,
    "score": 87.5
  }
}
```

### 2. Custom Data Files

For more control over test data, you can upload custom data files in supported formats.

---

## Supported File Formats

### CSV Format

CSV files provide a simple way to specify test data with one row per test iteration.

#### Structure

```csv
path_param1,path_param2,query_param1,query_param2,body_json
1001,active,category=electronics,sort=name,"{\"name\":\"Product1\",\"price\":99.99}"
1002,inactive,category=books,sort=price,"{\"name\":\"Product2\",\"price\":19.99}"
1003,active,category=electronics,sort=rating,"{\"name\":\"Product3\",\"price\":149.99}"
```

#### Column Naming Convention

- **Path Parameters**: Use the parameter name as defined in OpenAPI spec
- **Query Parameters**: Use `param_name` or `param_name=value` format
- **Body Data**: Use `body_json` column with JSON string

#### Example: User Management API

```csv
userId,status,searchTerm,body_json
101,active,john,"{\"name\":\"John Doe\",\"email\":\"john@example.com\",\"role\":\"user\"}"
102,inactive,jane,"{\"name\":\"Jane Smith\",\"email\":\"jane@example.com\",\"role\":\"admin\"}"
103,active,bob,"{\"name\":\"Bob Wilson\",\"email\":\"bob@example.com\",\"role\":\"user\"}"
```

#### Best Practices for CSV

1. **Headers are required** - First row must contain column names
2. **Escape quotes** - Use `""` for quotes within JSON
3. **Consistent data types** - Keep data types consistent within columns
4. **No empty rows** - Remove empty rows to avoid errors

### JSON Format

JSON files provide more flexibility and support complex nested data structures.

#### Structure

```json
[
  {
    "path_params": {
      "id": 1001,
      "status": "active"
    },
    "query_params": {
      "category": "electronics",
      "sort": "name",
      "page": 1
    },
    "body": {
      "name": "Product 1",
      "price": 99.99,
      "description": "High-quality electronic device",
      "tags": ["electronics", "gadget", "popular"],
      "metadata": {
        "supplier": "TechCorp",
        "warranty": 24
      }
    }
  },
  {
    "path_params": {
      "id": 1002,
      "status": "inactive"
    },
    "query_params": {
      "category": "books",
      "sort": "price",
      "page": 1
    },
    "body": {
      "name": "Product 2",
      "price": 19.99,
      "description": "Educational book",
      "tags": ["books", "education"],
      "metadata": {
        "supplier": "BookWorld",
        "warranty": 0
      }
    }
  }
]
```

#### JSON Data Structure

Each object in the array represents one test iteration with:

- **`path_params`** (object): Path parameter values
- **`query_params`** (object): Query parameter values  
- **`body`** (object): Request body data
- **`headers`** (object, optional): Custom headers for this iteration

#### Best Practices for JSON

1. **Validate JSON** - Ensure valid JSON syntax
2. **Consistent structure** - All objects should have the same structure
3. **Appropriate data types** - Use correct JSON types (string, number, boolean, array, object)
4. **Reasonable file size** - Keep under 10MB for good performance

### Excel Format (.xlsx)

Excel files are supported for users who prefer spreadsheet tools.

#### Structure

Similar to CSV but with Excel's additional features:

- **Sheet Name**: Use first sheet or name it "TestData"
- **Headers**: First row contains column names
- **Data Types**: Excel will auto-detect types
- **Formulas**: Supported for generating dynamic data

#### Example Excel Structure

| userId | userType | searchQuery | body_json |
|--------|----------|-------------|-----------|
| 1001 | premium | electronics | {"name":"John","email":"john@example.com"} |
| 1002 | standard | books | {"name":"Jane","email":"jane@example.com"} |
| 1003 | premium | clothing | {"name":"Bob","email":"bob@example.com"} |

#### Excel Best Practices

1. **Use simple data types** - Avoid complex Excel features
2. **Export to CSV** - For compatibility, consider exporting to CSV
3. **Check encoding** - Ensure proper character encoding

---

## Data Mapping

### Path Parameters

Path parameters are extracted from the endpoint path and matched with your data.

**Endpoint**: `GET /users/{userId}/orders/{orderId}`

**Data Mapping**:
```json
{
  "path_params": {
    "userId": 1234,
    "orderId": 5678
  }
}
```

**URL Result**: `GET /users/1234/orders/5678`

### Query Parameters

Query parameters are appended to the URL.

**Data**:
```json
{
  "query_params": {
    "page": 2,
    "limit": 50,
    "filter": "active",
    "sort": "created_date"
  }
}
```

**URL Result**: `GET /users?page=2&limit=50&filter=active&sort=created_date`

### Request Body

Request body data is sent as JSON payload for POST, PUT, PATCH requests.

**Data**:
```json
{
  "body": {
    "name": "John Doe",
    "email": "john@example.com",
    "preferences": {
      "newsletter": true,
      "notifications": false
    },
    "tags": ["customer", "premium"]
  }
}
```

**HTTP Request Body**:
```json
{
  "name": "John Doe",
  "email": "john@example.com", 
  "preferences": {
    "newsletter": true,
    "notifications": false
  },
  "tags": ["customer", "premium"]
}
```

---

## Data Iteration

### Cycling Through Data

LoadTester cycles through your provided data during the test:

1. **Sequential**: Data is used in order from first to last
2. **Restart**: When reaching the end, starts from the beginning
3. **Random**: Optionally, data can be selected randomly

### Example with 3 Users, 5 Test Iterations

```
Iteration 1: User 1 data
Iteration 2: User 2 data  
Iteration 3: User 3 data
Iteration 4: User 1 data (restart)
Iteration 5: User 2 data
```

### Data Volume Recommendations

- **Small datasets** (1-10 records): Good for functional testing
- **Medium datasets** (10-100 records): Suitable for load testing
- **Large datasets** (100+ records): Best for comprehensive testing

---

## Validation and Error Handling

### Data Validation

LoadTester validates your data against the OpenAPI specification:

1. **Schema Compliance**: Data types match OpenAPI schema
2. **Required Fields**: All required parameters are present
3. **Format Validation**: Emails, dates, URLs are properly formatted
4. **Constraints**: Min/max values, string lengths, enum values

### Common Validation Errors

#### Missing Required Parameters
```
Error: Missing required path parameter 'userId' in row 3
```

#### Invalid Data Types
```
Error: Expected integer for 'age' but got string 'twenty-five' in row 5
```

#### Format Violations
```
Error: Invalid email format 'not-an-email' in row 2
```

### Error Reporting

When validation fails, LoadTester provides:
- **Row number** (for CSV/Excel)
- **Field name** that failed
- **Expected format** vs. actual value
- **Suggested corrections**

---

## Advanced Features

### Dynamic Data Generation

You can mix static data with dynamic generation:

```json
{
  "path_params": {
    "id": "{{generate_id}}"
  },
  "query_params": {
    "timestamp": "{{current_timestamp}}"
  },
  "body": {
    "name": "Static Name",
    "email": "{{generate_email}}"
  }
}
```

**Available Generators**:
- `{{generate_id}}`: Random integer ID
- `{{generate_email}}`: Random email address
- `{{current_timestamp}}`: Current timestamp
- `{{random_string}}`: Random string
- `{{uuid}}`: UUID v4

### Conditional Data

Use different data based on test conditions:

```json
{
  "scenarios": {
    "light_load": {
      "path_params": {"id": 1001}
    },
    "heavy_load": {
      "path_params": {"id": 2001}
    }
  }
}
```

### Data Relationships

Maintain relationships between different parameters:

```json
{
  "related_data": [
    {
      "user_id": 1001,
      "order_id": 2001,
      "product_ids": [3001, 3002]
    },
    {
      "user_id": 1002, 
      "order_id": 2002,
      "product_ids": [3003, 3004, 3005]
    }
  ]
}
```

---

## File Size and Performance

### Limits

- **Maximum file size**: 10MB
- **Maximum records**: 10,000 (recommended)
- **Processing time**: Larger files take longer to validate

### Performance Tips

1. **Optimize file size**: Remove unnecessary columns/data
2. **Use appropriate formats**: JSON for complex data, CSV for simple data
3. **Pre-validate data**: Check data locally before uploading
4. **Split large datasets**: Use multiple smaller files if needed

### Memory Usage

| Records | Approximate Memory |
|---------|-------------------|
| 100 | ~1MB |
| 1,000 | ~10MB |
| 10,000 | ~100MB |

---

## Examples

### E-commerce API Test Data

**CSV Format**:
```csv
productId,category,userId,body_json
101,electronics,1001,"{\"quantity\":2,\"color\":\"red\"}"
102,books,1002,"{\"quantity\":1,\"format\":\"hardcover\"}"
103,clothing,1003,"{\"quantity\":3,\"size\":\"M\"}"
```

**JSON Format**:
```json
[
  {
    "path_params": {"productId": 101},
    "query_params": {"category": "electronics"},
    "headers": {"User-ID": "1001"},
    "body": {
      "quantity": 2,
      "color": "red",
      "priority": "standard"
    }
  }
]
```

### User Management API

**JSON Format**:
```json
[
  {
    "path_params": {"userId": 1001},
    "body": {
      "name": "John Doe",
      "email": "john.doe@example.com",
      "profile": {
        "age": 30,
        "location": "New York",
        "interests": ["technology", "sports"]
      },
      "settings": {
        "notifications": true,
        "privacy": "public"
      }
    }
  }
]
```

### API Authentication Test

**CSV with Different Auth Types**:
```csv
endpoint,auth_type,token,body_json
/public/info,none,,"{\"request\":\"info\"}"
/user/profile,bearer,eyJhbGciOiJIUzI1NiIs...,"{\"fields\":[\"name\",\"email\"]}"
/admin/users,api_key,sk-1234567890abcdef,"{\"action\":\"list\",\"limit\":10}"
```

---

## Troubleshooting

### Common Issues

#### File Upload Fails
- Check file size (must be < 10MB)
- Verify file format (CSV, JSON, XLSX only)
- Ensure proper file encoding (UTF-8)

#### Data Validation Errors
- Check OpenAPI schema compliance
- Verify required fields are present
- Validate data types match expectations

#### Performance Issues
- Reduce file size
- Simplify data structure
- Use CSV instead of JSON for simple data

### Best Practices Summary

1. **Start small**: Begin with a few test records
2. **Validate early**: Check data format before uploading
3. **Use mock data**: Let AI generate data when possible
4. **Keep it simple**: Use the simplest format that meets your needs
5. **Document your data**: Include comments or documentation for complex datasets
6. **Test locally**: Validate your data files before using in load tests