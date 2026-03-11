# OpenAPI Test Generator

Generate **pytest API tests automatically from OpenAPI specifications**.

This CLI tool reads an OpenAPI spec and produces starter API tests including:

- happy-path tests
- negative tests
- schema-based payload generation
- response validation

The goal is to reduce repetitive API test setup and provide a strong starting point for automated testing.

---

# Features

## OpenAPI Support

- Works with **JSON and YAML** OpenAPI specs
- Automatically discovers API endpoints
- Supports common HTTP methods:
  - GET
  - POST
  - PUT
  - PATCH
  - DELETE

## Smart Payload Generation

Request payloads are generated from OpenAPI schemas with support for:

- `example` values
- `default` values
- required fields
- enum fields
- `$ref` schema resolution

Example generated payload:

```python
payload = {'name': 'Ryan', 'email': 'ryan@example.com', 'role': 'admin'}
```

---

## Automatic Negative Tests

The generator automatically creates tests for common invalid scenarios:

- missing required fields
- invalid enum values

Example:

```python
def test_post_users_missing_name():
    payload = {'email': 'ryan@example.com', 'role': 'admin'}
    response = requests.post(f"{BASE_URL}/users", json=payload)
    assert response.status_code == 400
```

---

## Response Validation

Generated tests verify:

- expected response codes from the OpenAPI spec
- response JSON schema using `jsonschema`

Example:

```python
assert response.status_code == 201

data = response.json()
jsonschema.validate(data, schema)
```

---

## CLI Options

Generate tests from an OpenAPI spec:

```bash
python main.py openapi.yaml
```

Optional arguments:

```bash
--output <file>
--base-url <url>
```

Example:

```bash
python main.py openapi.yaml --base-url https://api.dev.com
```

Default output file:

```
generated/generated_api_tests.py
```

---

# Example

## Input (OpenAPI)

```yaml
paths:
  /users:
    post:
      summary: Create user
      requestBody:
        content:
          application/json:
            schema:
              $ref: "#/components/schemas/UserCreate"
      responses:
        "201":
          description: User created
        "400":
          description: Invalid request

components:
  schemas:
    UserCreate:
      type: object
      required: ["name", "email"]
      properties:
        name:
          type: string
          example: Ryan
        email:
          type: string
          example: ryan@example.com
        role:
          type: string
          enum: ["admin", "user"]
          example: admin
```

---

## Generated Tests

Running:

```bash
python main.py openapi.yaml --base-url https://api.dev.com
```

Produces:

```
Generated generated/generated_api_tests.py with 4 test(s).
```

Generated file:

```python
import requests
import jsonschema

BASE_URL = "https://api.dev.com"


def test_post_users():
    payload = {'name': 'Ryan', 'email': 'ryan@example.com', 'role': 'admin'}
    response = requests.post(f"{BASE_URL}/users", json=payload)
    assert response.status_code == 201


def test_post_users_missing_name():
    payload = {'email': 'ryan@example.com', 'role': 'admin'}
    response = requests.post(f"{BASE_URL}/users", json=payload)
    assert response.status_code == 400


def test_post_users_missing_email():
    payload = {'name': 'Ryan', 'role': 'admin'}
    response = requests.post(f"{BASE_URL}/users", json=payload)
    assert response.status_code == 400


def test_post_users_invalid_role_enum():
    payload = {'name': 'Ryan', 'email': 'ryan@example.com', 'role': 'invalid_enum_value'}
    response = requests.post(f"{BASE_URL}/users", json=payload)
    assert response.status_code == 400
```

---

# Installation

Clone the repository:

```bash
git clone https://github.com/yourusername/openapi-test-generator.git
cd openapi-test-generator
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

# Running Tests

Run the unit tests:

```bash
python -m pytest
```

Example output:

```
25 passed in 0.03s
```

---

# Project Structure

```
openapi-test-generator/
│
├── main.py            # CLI entry point
├── parser.py          # OpenAPI loading and endpoint extraction
├── generator.py       # Test generation logic
│
├── tests/
│   └── test_generator.py
│
├── requirements.txt
└── README.md
```

---

# Future Improvements

Possible future enhancements:

- authentication support (Bearer tokens / API keys)
- response validation for additional response codes
- nested schema negative tests
- generate tests for all documented response codes
- package as an installable CLI tool
- CI integration

---

# License

MIT