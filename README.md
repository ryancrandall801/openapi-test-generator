# OpenAPI Test Generator

Turn your **OpenAPI spec into a runnable pytest suite.**

Generate Python API tests automatically from OpenAPI JSON or YAML.

---

## Demo

![Demo](docs/demo.gif)

---

## Quickstart

Install locally:

```bash
pip install -e .
```

Generate tests:

```bash
openapi-testgen openapi.json
```

Run them:

```bash
python -m pytest generated/generated_api_tests.py -vv
```

---

## Example

Generate tests from a public OpenAPI spec:

```bash
openapi-testgen https://petstore3.swagger.io/api/v3/openapi.json --methods GET
```

Run:

```bash
pytest generated/generated_api_tests.py
```

---

## Features

- Generate pytest tests from OpenAPI specs
- JSON and YAML support
- Local files and remote URLs
- Negative tests
- Response schema validation
- Auth header support
- Method filtering
- Tag filtering
- Config file support
- Web demo UI

---

## CLI Usage

Basic usage:

```bash
openapi-testgen spec.json
```

Custom output file:

```bash
openapi-testgen spec.json --output tests/generated_api_tests.py
```

Filter by method:

```bash
openapi-testgen spec.json --methods GET,POST
```

Filter by tags:

```bash
openapi-testgen spec.json --tags Users
```

Auth headers:

```bash
openapi-testgen spec.json \
  --auth-header-name Authorization \
  --auth-token-env API_TOKEN \
  --auth-scheme Bearer
```

---

## Config File

Create `openapi-testgen.yaml`:

```yaml
base_url: https://reqres.in
methods: GET
tags: Legacy
```

Then run:

```bash
openapi-testgen reqres_openapi.json
```

---

## Web Demo

The browser demo allows you to:

- paste an OpenAPI spec URL
- preview generated pytest tests
- copy generated tests
- download the `.py` file

Example demo specs:

- Swagger Petstore
- ReqRes
- GitHub API

---

## Project Structure

```
openapi_test_generator/
  cli.py
  parser.py
  generator.py

tests/

website/

generated/

docs/
  demo.gif
```

---

## Why this tool exists

Writing API tests is repetitive.

OpenAPI specs already describe:

- endpoints
- request schemas
- parameters
- responses

This tool turns that information into runnable pytest tests instantly.

---

## License

MIT