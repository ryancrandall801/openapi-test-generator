from openapi_test_generator.generator import (
    format_python_literal,
    generate_invalid_enum_payloads,
    generate_missing_required_payloads,
    generate_sample_value,
    generate_test_file,
    get_error_status_code,
    get_json_request_body,
    get_response_schema,
    get_schema_from_operation,
    get_success_status_code,
    replace_path_params,
    resolve_ref,
    sanitize_path_for_name,
    write_test_file,
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
                    },
                    "responses": {
                        "201": {
                            "description": "Created"
                        }
                    },
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
    assert "assert response.status_code == 201" in output


def test_generate_test_file_replaces_path_params_in_output() -> None:
    spec = make_sample_spec()
    endpoints = [("DELETE", "/users/{id}", {})]

    output = generate_test_file(endpoints, spec)

    assert 'response = requests.delete(f"{BASE_URL}/users/1")' in output


def test_generate_sample_value_uses_example_when_present() -> None:
    spec = make_sample_spec()

    value = generate_sample_value(
        {"type": "string", "example": "Ryan"},
        spec,
    )

    assert value == "Ryan"


def test_generate_sample_value_uses_default_when_present() -> None:
    spec = make_sample_spec()

    value = generate_sample_value(
        {"type": "integer", "default": 25},
        spec,
    )

    assert value == 25


def test_generate_sample_value_handles_required_example_and_default_fields() -> None:
    spec = {
        "components": {
            "schemas": {
                "UserCreate": {
                    "type": "object",
                    "required": ["name", "email"],
                    "properties": {
                        "name": {"type": "string", "example": "Ryan"},
                        "email": {"type": "string", "example": "ryan@example.com"},
                        "age": {"type": "integer", "default": 25},
                        "active": {"type": "boolean"},
                    },
                }
            }
        }
    }

    value = generate_sample_value(
        {"$ref": "#/components/schemas/UserCreate"},
        spec,
    )

    assert value == {
        "name": "Ryan",
        "email": "ryan@example.com",
        "age": 25,
        "active": True,
    }


def test_generate_test_file_uses_example_and_default_values() -> None:
    spec = {
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
                    "required": ["name"],
                    "properties": {
                        "name": {"type": "string", "example": "Ryan"},
                        "age": {"type": "integer", "default": 25},
                    },
                }
            }
        },
    }


def test_generate_test_file_uses_custom_base_url() -> None:
    spec = make_sample_spec()
    endpoints = [("POST", "/users", spec["paths"]["/users"]["post"])]

    output = generate_test_file(endpoints, spec, "https://api.dev.com")

    assert 'BASE_URL = "https://api.dev.com"' in output


def test_get_success_status_code_returns_first_2xx_code() -> None:
    operation = {
        "responses": {
            "201": {"description": "Created"},
            "400": {"description": "Bad request"},
        }
    }

    result = get_success_status_code(operation)

    assert result == "201"


def test_get_success_status_code_returns_none_when_no_2xx_exists() -> None:
    operation = {
        "responses": {
            "400": {"description": "Bad request"},
            "404": {"description": "Not found"},
        }
    }

    result = get_success_status_code(operation)

    assert result is None


def test_generate_test_file_uses_documented_success_status_code() -> None:
    spec = {
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
                    },
                    "responses": {
                        "201": {
                            "description": "Created"
                        }
                    },
                }
            }
        },
        "components": {
            "schemas": {
                "UserCreate": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "example": "Ryan"},
                    },
                }
            }
        },
    }

    endpoints = [("POST", "/users", spec["paths"]["/users"]["post"])]

    output = generate_test_file(endpoints, spec)

    assert "assert response.status_code == 201" in output


def test_get_error_status_code_prefers_400() -> None:
    operation = {
        "responses": {
            "201": {"description": "Created"},
            "400": {"description": "Bad request"},
            "422": {"description": "Validation error"},
        }
    }

    result = get_error_status_code(operation)

    assert result == "400"


def test_get_error_status_code_falls_back_to_422() -> None:
    operation = {
        "responses": {
            "201": {"description": "Created"},
            "422": {"description": "Validation error"},
        }
    }

    result = get_error_status_code(operation)

    assert result == "422"


def test_get_error_status_code_returns_first_4xx_when_400_and_422_missing() -> None:
    operation = {
        "responses": {
            "201": {"description": "Created"},
            "404": {"description": "Not found"},
        }
    }

    result = get_error_status_code(operation)

    assert result == "404"


def test_get_error_status_code_returns_none_when_no_4xx_exists() -> None:
    operation = {
        "responses": {
            "200": {"description": "OK"},
            "500": {"description": "Server error"},
        }
    }

    result = get_error_status_code(operation)

    assert result is None


def test_generate_test_file_uses_documented_4xx_response_code_in_negative_tests() -> None:
    spec = {
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
                    },
                    "responses": {
                        "201": {"description": "Created"},
                        "400": {"description": "Bad request"},
                    },
                }
            }
        },
        "components": {
            "schemas": {
                "UserCreate": {
                    "type": "object",
                    "required": ["name"],
                    "properties": {
                        "name": {"type": "string", "example": "Ryan"},
                        "role": {"type": "string", "enum": ["admin", "user"], "example": "admin"},
                    },
                }
            }
        },
    }

    endpoints = [("POST", "/users", spec["paths"]["/users"]["post"])]

    output = generate_test_file(endpoints, spec)

    assert "def test_post_users_missing_name():" in output
    assert "def test_post_users_invalid_role_enum():" in output
    assert "assert response.status_code == 400" in output


def test_write_test_file_creates_parent_directory(tmp_path) -> None:
    output_path = tmp_path / "generated" / "generated_api_tests.py"
    content = "def test_example():\n    pass\n"

    write_test_file(output_path, content)

    assert output_path.exists()
    assert output_path.read_text(encoding="utf-8") == content