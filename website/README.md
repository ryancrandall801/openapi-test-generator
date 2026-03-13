# OpenAPI Test Generator

Generate pytest API tests instantly from an OpenAPI spec.

Stop writing repetitive API tests.

---

## Demo

![Demo](demo.gif)

---

## Example

Input OpenAPI spec:

https://petstore3.swagger.io/api/v3/openapi.json

Generate tests:

```bash
openapi-testgen https://petstore3.swagger.io/api/v3/openapi.json
```

Run tests:

```bash
pytest generated/generated_api_tests.py
```

Result:

```
collected 34 tests
34 passed
```

---

## What It Generates

For every endpoint the generator creates:

• positive API tests  
• negative validation tests  
• invalid enum tests  
• JSON schema validation  

Example generated test:

```python
def test_post_pet():
    payload = {
        "name": "doggie",
        "photoUrls": ["string"]
    }

    response = requests.post(f"{BASE_URL}/pet", json=payload)

    assert response.status_code == 200
    jsonschema.validate(response.json(), schema)
```

---

## Install

```bash
pip install openapi-testgen
```

---

## CLI Usage

```bash
openapi-testgen <openapi-spec>
```

Example:

```bash
openapi-testgen https://petstore3.swagger.io/api/v3/openapi.json
```

---

## Options

```
--methods GET,POST
--tags pet
--base-url https://api.example.com
--auth-header-name Authorization
--auth-token-env API_TOKEN
```

---

## Why This Exists

Writing API tests is repetitive.

If you already have an OpenAPI spec, the tests can be generated automatically.

---

## Website Demo

Try it in the browser:

https://your-site.com

---

## License

MIT