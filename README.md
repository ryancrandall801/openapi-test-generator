# OpenAPI Test Generator

Turn your **OpenAPI specification into a runnable pytest suite instantly.**

Generate **real API tests automatically** from an OpenAPI spec.

The generator reads an OpenAPI spec (JSON or YAML) and produces a pytest test file that:

- Calls real endpoints
- Generates request payloads
- Validates response status codes
- Validates response schemas
- Generates negative tests (missing fields / invalid enums)

---

# 10-Second Quickstart

Generate a pytest API test suite from an OpenAPI spec in **two commands**.

```bash
pip install -e .
openapi-testgen openapi.json
```

This generates:

```
generated/generated_api_tests.py
```

Run the tests:

```bash
python -m pytest generated/generated_api_tests.py -vv
```

That’s it — your OpenAPI spec is now a runnable pytest suite.

---

# Demo

Generate API tests from an OpenAPI spec in seconds.

![Demo](docs/demo.gif)

---

# Example (Real API)

Example using the public **ReqRes API**.

Set your API key first:

```powershell
$env:REQRES_API_KEY="your_reqres_public_key"
```

Then run:

```powershell
openapi-testgen reqres_openapi.json
python -m pytest generated/generated_api_tests.py -vv
```

Result:

```
4 passed in 1.55s
```

These tests make **real HTTP calls** and validate responses against the API schema.

---

# Features

✔ Generate pytest tests from OpenAPI specs  
✔ Supports JSON and YAML specs  
✔ Supports local files or spec URLs  
✔ Generates request payloads automatically  
✔ Generates query parameters automatically  
✔ Validates responses with `jsonschema`  
✔ Generates negative tests automatically  
✔ Supports auth headers  
✔ Filter by HTTP methods  
✔ Filter by OpenAPI tags  
✔ Supports config files for cleaner workflows

---

# Installation

Clone the repository and install locally:

```bash
pip install -e .
```

The CLI command becomes available:

```bash
openapi-testgen
```

---

# Usage

## Generate tests from a local spec

```bash
openapi-testgen openapi.json
```

This creates:

```
generated/generated_api_tests.py
```

---

## Generate tests from an OpenAPI URL

```bash
openapi-testgen https://api.example.com/openapi.json
```

---

## Specify a base URL

```bash
openapi-testgen openapi.json --base-url https://api.example.com
```

---

## Authentication headers

For APIs requiring authentication:

```bash
openapi-testgen openapi.json \
  --auth-header-name Authorization \
  --auth-token-env API_TOKEN \
  --auth-scheme Bearer
```

Generated tests will include:

```python
HEADERS = {
    "Authorization": f"Bearer {os.environ['API_TOKEN']}"
}
```

---

## Method filtering

Generate tests only for certain HTTP methods.

```bash
openapi-testgen openapi.json --methods GET
```

or:

```bash
openapi-testgen openapi.json --methods GET,POST
```

---

## Tag filtering

Generate tests only for endpoints with specific OpenAPI tags.

```bash
openapi-testgen openapi.json --tags Users
```

or multiple tags:

```bash
openapi-testgen openapi.json --tags Users,Auth
```

---

## Config file support

You can keep generator options in a config file for shorter commands.

Create `openapi-testgen.yaml` in the repo root:

```yaml
base_url: https://reqres.in
auth_header_name: x-api-key
auth_token_env: REQRES_API_KEY
methods: GET
tags: Legacy
```

Then run:

```bash
openapi-testgen reqres_openapi.json
```

---

# Running the Generated Tests

```bash
python -m pytest generated/generated_api_tests.py -vv
```

The generated tests will:

- call the API
- assert status codes
- validate response schemas
- run negative tests where applicable

---

# Example Generated Test

```python
def test_get_api_users():
    response = requests.get(f"{BASE_URL}/api/users", headers=HEADERS)
    assert response.status_code == 200

    content_type = response.headers.get("Content-Type", "")
    assert "application/json" in content_type

    data = response.json()
    schema = {...}
    jsonschema.validate(data, schema)
```

---

# Project Structure

```
openapi_test_generator/
    cli.py
    parser.py
    generator.py

tests/
    test_parser.py
    test_generator.py

generated/
    generated_api_tests.py

docs/
    demo.gif
```

---

# Roadmap

Potential future improvements:

- Automatic auth detection from OpenAPI security schemes
- Better path parameter examples
- Response body sampling
- CI integration examples
- Web interface for generating tests
- Hosted API test generation and monitoring

---

# Why This Tool Exists

Writing API tests manually is repetitive.

OpenAPI already describes:

- endpoints
- schemas
- parameters
- request bodies
- responses

This tool converts that specification into **working tests automatically**.

---

# License

MIT