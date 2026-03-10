# OpenAPI Test Generator

A CLI tool that reads an OpenAPI specification and generates starter **pytest API tests** automatically.

This project was built to reduce the repetitive work involved in writing API tests by generating a basic test suite directly from an OpenAPI spec.

---

## Features

- Generate pytest tests from OpenAPI specs
- Supports **JSON and YAML** OpenAPI files
- Automatically discovers API endpoints
- Generates starter tests for HTTP methods:
  - GET
  - POST
  - PUT
  - PATCH
  - DELETE
- Generates sample request bodies from OpenAPI schemas
- Resolves local `$ref` schemas from `components/schemas`
- Handles path parameters (e.g. `/users/{id}` → `/users/1`)
- CLI interface with configurable output file
- Unit tests for generator logic

---

## Installation

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

## Usage

Generate tests from an OpenAPI spec:

```bash
python main.py sample_openapi.json
```

Or using a YAML spec:

```bash
python main.py sample_openapi.yaml
```

By default the generated tests are written to:

```
generated_api_tests.py
```

---

### Custom output file

```bash
python main.py sample_openapi.yaml --output users_api_tests.py
```

---

## Example

### Input (OpenAPI)

```yaml
paths:
  /users:
    post:
      requestBody:
        content:
          application/json:
            schema:
              $ref: "#/components/schemas/UserCreate"

components:
  schemas:
    UserCreate:
      type: object
      properties:
        name:
          type: string
        age:
          type: integer
        active:
          type: boolean
```

### Generated pytest test

```python
import requests

BASE_URL = "http://localhost:8000"


def test_post_users():
    payload = {'name': 'string', 'age': 0, 'active': True}
    response = requests.post(f"{BASE_URL}/users", json=payload)
    assert response.status_code < 500
```

---

## Running Tests

Run unit tests with pytest:

```bash
python -m pytest
```

Example output:

```
15 passed in 0.02s
```

---

## Project Structure

```
openapi-test-generator/
│
├── main.py            # CLI entry point
├── parser.py          # OpenAPI loading and endpoint extraction
├── generator.py       # Test generation logic
│
├── tests/             # Unit tests
│   └── test_generator.py
│
├── requirements.txt
└── README.md
```

---

## Future Improvements

Potential enhancements for the tool:

- Support OpenAPI `example` and `default` values
- Respect `required` schema fields
- Generate negative test cases
- Authentication support (Bearer / API keys)
- Package as a pip-installable CLI tool
- CI integration

---

## License

MIT