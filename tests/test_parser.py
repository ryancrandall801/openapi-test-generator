from openapi_test_generator.parser import extract_endpoints


def test_extract_endpoints_returns_methods_and_paths():
    spec = {
        "paths": {
            "/users": {
                "get": {"summary": "List users"},
                "post": {"summary": "Create user"},
            }
        }
    }

    endpoints = extract_endpoints(spec)

    assert ("GET", "/users", {"summary": "List users"}) in endpoints
    assert ("POST", "/users", {"summary": "Create user"}) in endpoints


def test_extract_endpoints_ignores_non_http_keys():
    spec = {
        "paths": {
            "/users": {
                "parameters": [],
                "get": {"summary": "List users"},
            }
        }
    }

    endpoints = extract_endpoints(spec)

    assert len(endpoints) == 1
    assert endpoints[0][0] == "GET"


from openapi_test_generator.parser import load_openapi_spec
from pathlib import Path
import json


def test_load_openapi_spec_json(tmp_path):
    data = {"openapi": "3.0.0", "paths": {}}

    file = tmp_path / "spec.json"
    file.write_text(json.dumps(data))

    result = load_openapi_spec(file)

    assert result["openapi"] == "3.0.0"