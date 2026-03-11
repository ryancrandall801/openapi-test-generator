from openapi_test_generator.generator import (
    build_headers_code,
    build_request_call,
    dereference_schema,
    format_python_literal,
    generate_invalid_enum_payloads,
    generate_missing_required_payloads,
    generate_sample_value,
    generate_test_file,
    generate_path_param_value,
    get_path_parameters,
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
    spec = {}
    operation = {
        "parameters": [
            {
                "name": "id",
                "in": "path",
                "required": True,
                "schema": {"type": "integer", "minimum": 1},
            }
        ]
    }

    assert replace_path_params("/users/{id}", operation, spec) == "/users/1"


def test_replace_path_params_replaces_multiple_integer_params() -> None:
    spec = {}
    operation = {
        "parameters": [
            {
                "name": "team_id",
                "in": "path",
                "required": True,
                "schema": {"type": "integer", "minimum": 1},
            },
            {
                "name": "id",
                "in": "path",
                "required": True,
                "schema": {"type": "integer", "minimum": 1},
            },
        ]
    }

    assert (
        replace_path_params("/teams/{team_id}/users/{id}", operation, spec)
        == "/teams/1/users/1"
    )


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
    operation = {
        "parameters": [
            {
                "name": "id",
                "in": "path",
                "required": True,
                "schema": {"type": "integer", "minimum": 1},
            }
        ]
    }
    endpoints = [("DELETE", "/users/{id}", operation)]

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


def test_build_headers_code_returns_none_when_auth_not_configured() -> None:
    result = build_headers_code(None, None, None)

    assert result is None


def test_build_headers_code_generates_bearer_header() -> None:
    result = build_headers_code(
        "Authorization",
        "OPENAPI_TESTGEN_TOKEN",
        "Bearer",
    )

    assert result == (
        "HEADERS = {\n"
        '    "Authorization": f"Bearer {os.environ[\'OPENAPI_TESTGEN_TOKEN\']}"\n'
        "}"
    )


def test_build_headers_code_generates_raw_header() -> None:
    result = build_headers_code(
        "X-API-Key",
        "OPENAPI_TESTGEN_API_KEY",
        None,
    )

    assert result == (
        "HEADERS = {\n"
        '    "X-API-Key": os.environ["OPENAPI_TESTGEN_API_KEY"]\n'
        "}"
    )


def test_build_request_call_includes_headers_and_payload() -> None:
    result = build_request_call(
        "post",
        "/users",
        {"name": "Ryan"},
        None,
        True,
    )

    assert result == 'response = requests.post(f"{BASE_URL}/users", json=payload, headers=HEADERS)'


def test_generate_test_file_includes_auth_header_setup_for_bearer_token() -> None:
    spec = make_sample_spec()
    endpoints = [("POST", "/users", spec["paths"]["/users"]["post"])]

    output = generate_test_file(
        endpoints,
        spec,
        "https://api.dev.com",
        auth_header_name="Authorization",
        auth_token_env="OPENAPI_TESTGEN_TOKEN",
        auth_scheme="Bearer",
    )

    assert "import os" in output
    assert 'BASE_URL = "https://api.dev.com"' in output
    assert 'HEADERS = {' in output
    assert '    "Authorization": f"Bearer {os.environ[\'OPENAPI_TESTGEN_TOKEN\']}"' in output
    assert 'headers=HEADERS' in output


def test_generate_test_file_includes_auth_header_setup_for_api_key() -> None:
    spec = make_sample_spec()
    endpoints = [("POST", "/users", spec["paths"]["/users"]["post"])]

    output = generate_test_file(
        endpoints,
        spec,
        auth_header_name="X-API-Key",
        auth_token_env="OPENAPI_TESTGEN_API_KEY",
    )

    assert '    "X-API-Key": os.environ["OPENAPI_TESTGEN_API_KEY"]' in output
    assert 'headers=HEADERS' in output


def test_dereference_schema_resolves_nested_refs() -> None:
    spec = {
        "components": {
            "schemas": {
                "User": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "integer"},
                        "email": {"type": "string"},
                    },
                    "required": ["id", "email"],
                },
                "UserResponse": {
                    "type": "object",
                    "properties": {
                        "data": {"$ref": "#/components/schemas/User"},
                    },
                    "required": ["data"],
                },
            }
        }
    }

    schema = {"$ref": "#/components/schemas/UserResponse"}

    result = dereference_schema(schema, spec)

    assert result == {
        "type": "object",
        "properties": {
            "data": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer"},
                    "email": {"type": "string"},
                },
                "required": ["id", "email"],
            }
        },
        "required": ["data"],
    }


def test_replace_path_params_replaces_integer_param_with_sample_value() -> None:
    spec = {}
    operation = {
        "parameters": [
            {
                "name": "id",
                "in": "path",
                "required": True,
                "schema": {"type": "integer", "minimum": 1},
            }
        ]
    }

    assert replace_path_params("/users/{id}", operation, spec) == "/users/1"


def test_replace_path_params_uses_string_placeholder_for_slug() -> None:
    spec = {}
    operation = {
        "parameters": [
            {
                "name": "slug",
                "in": "path",
                "required": True,
                "schema": {"type": "string"},
            }
        ]
    }

    assert (
        replace_path_params("/collections/{slug}", operation, spec)
        == "/collections/example-slug"
    )


def test_replace_path_params_uses_parameter_example_when_present() -> None:
    spec = {}
    operation = {
        "parameters": [
            {
                "name": "slug",
                "in": "path",
                "required": True,
                "example": "users",
                "schema": {"type": "string"},
            }
        ]
    }

    assert replace_path_params("/collections/{slug}", operation, spec) == "/collections/users"


def test_generate_path_param_value_uses_schema_example_when_present() -> None:
    spec = {}
    parameter = {
        "name": "recordId",
        "in": "path",
        "required": True,
        "schema": {
            "type": "string",
            "example": "abc123",
        },
    }

    assert generate_path_param_value(parameter, spec) == "abc123"


def test_generate_test_file_checks_content_type_before_json_validation() -> None:
    spec = {
        "paths": {
            "/users": {
                "get": {
                    "responses": {
                        "200": {
                            "description": "Successful response",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "id": {"type": "integer"}
                                        },
                                        "required": ["id"],
                                    }
                                }
                            },
                        }
                    },
                }
            }
        }
    }

    endpoints = [("GET", "/users", spec["paths"]["/users"]["get"])]

    output = generate_test_file(endpoints, spec)

    assert 'content_type = response.headers.get("Content-Type", "")' in output
    assert 'assert "application/json" in content_type' in output
    assert "data = response.json()" in output


def test_build_request_call_includes_query_params() -> None:
    result = build_request_call(
        "get",
        "/users",
        None,
        {"page": 1},
        True,
    )

    assert result == 'response = requests.get(f"{BASE_URL}/users", params={\'page\': 1}, headers=HEADERS)'