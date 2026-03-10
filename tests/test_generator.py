from generator import (
    format_python_literal,
    generate_sample_value,
    generate_test_file,
    get_json_request_body,
    replace_path_params,
    resolve_ref,
    sanitize_path_for_name,
)


def make_sample_spec() -> dict:
    return {
        "openapi": "3.0.0",
        "info": {
            "title": "Sample API",
            "version": "1.0.0",
        },
        "paths": {
            "/users": {
                "post": {
                    "requestBody": {
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/UserCreate"
                                }
                            }
                        }
                    }
                }
            }
        },
        "components": {
            "schemas": {
                "UserCreate": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "age": {"type": "integer"},
                        "active": {"type": "boolean"},
                        "tags": {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                    },
                }
            }
        },
    }


def test_sanitize_path_for_name_removes_special_chars() -> None:
    assert sanitize_path_for_name("/users/{id}") == "users_id"


def test_sanitize_path_for_name_returns_root_for_slash() -> None:
    assert sanitize_path_for_name("/") == "root"


def test_replace_path_params_replaces_param_with_sample_value() -> None:
    assert replace_path_params("/users/{id}") == "/users/1"


def test_replace_path_params_replaces_multiple_params() -> None:
    assert replace_path_params("/teams/{team_id}/users/{id}") == "/teams/1/users/1"


def test_resolve_ref_returns_schema_from_components() -> None:
    spec = make_sample_spec()

    resolved = resolve_ref("#/components/schemas/UserCreate", spec)

    assert resolved == spec["components"]["schemas"]["UserCreate"]


def test_generate_sample_value_handles_string() -> None:
    spec = make_sample_spec()

    assert generate_sample_value({"type": "string"}, spec) == "string"


def test_generate_sample_value_handles_integer() -> None:
    spec = make_sample_spec()

    assert generate_sample_value({"type": "integer"}, spec) == 0


def test_generate_sample_value_handles_boolean() -> None:
    spec = make_sample_spec()

    assert generate_sample_value({"type": "boolean"}, spec) is True


def test_generate_sample_value_handles_array() -> None:
    spec = make_sample_spec()

    value = generate_sample_value(
        {
            "type": "array",
            "items": {"type": "string"},
        },
        spec,
    )

    assert value == ["string"]


def test_generate_sample_value_resolves_ref() -> None:
    spec = make_sample_spec()

    value = generate_sample_value(
        {"$ref": "#/components/schemas/UserCreate"},
        spec,
    )

    assert value == {
        "name": "string",
        "age": 0,
        "active": True,
        "tags": ["string"],
    }


def test_get_json_request_body_returns_none_when_missing() -> None:
    spec = make_sample_spec()
    operation = {}

    assert get_json_request_body(operation, spec) is None


def test_get_json_request_body_returns_generated_payload() -> None:
    spec = make_sample_spec()
    operation = spec["paths"]["/users"]["post"]

    payload = get_json_request_body(operation, spec)

    assert payload == {
        "name": "string",
        "age": 0,
        "active": True,
        "tags": ["string"],
    }


def test_format_python_literal_returns_valid_python_repr() -> None:
    value = {"active": True, "tags": ["string"]}

    result = format_python_literal(value)

    assert result == "{'active': True, 'tags': ['string']}"


def test_generate_test_file_includes_generated_post_test() -> None:
    spec = make_sample_spec()
    endpoints = [("POST", "/users", spec["paths"]["/users"]["post"])]

    output = generate_test_file(endpoints, spec)

    assert "def test_post_users():" in output
    assert "payload = {'name': 'string', 'age': 0, 'active': True, 'tags': ['string']}" in output
    assert 'response = requests.post(f"{BASE_URL}/users", json=payload)' in output


def test_generate_test_file_replaces_path_params_in_output() -> None:
    spec = make_sample_spec()
    endpoints = [("DELETE", "/users/{id}", {})]

    output = generate_test_file(endpoints, spec)

    assert 'response = requests.delete(f"{BASE_URL}/users/1")' in output