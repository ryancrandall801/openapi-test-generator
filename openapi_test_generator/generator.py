from pathlib import Path


def resolve_ref(ref: str, spec: dict) -> dict:
    """
    Resolve a local OpenAPI $ref like '#/components/schemas/User'.

    Only supports local refs for now.
    """
    if not ref.startswith("#/"):
        raise ValueError(f"Only local refs are supported right now: {ref}")

    current = spec
    parts = ref[2:].split("/")

    for part in parts:
        if part not in current:
            raise KeyError(f"Could not resolve ref: {ref}")
        current = current[part]

    if not isinstance(current, dict):
        raise ValueError(f"Resolved ref is not a schema object: {ref}")

    return current


def dereference_schema(schema: object, spec: dict) -> object:
    """Recursively resolve local $ref values inside a schema."""
    if isinstance(schema, dict):
        if "$ref" in schema:
            resolved = resolve_ref(schema["$ref"], spec)
            return dereference_schema(resolved, spec)

        return {
            key: dereference_schema(value, spec)
            for key, value in schema.items()
        }

    if isinstance(schema, list):
        return [dereference_schema(item, spec) for item in schema]

    return schema


def sanitize_path_for_name(path: str) -> str:
    """Convert an API path into something safe for a Python test name."""
    cleaned = path.strip("/")
    cleaned = cleaned.replace("/", "_")
    cleaned = cleaned.replace("{", "")
    cleaned = cleaned.replace("}", "")
    cleaned = cleaned.replace("-", "_")
    return cleaned or "root"


def get_path_parameters(operation: dict) -> list[dict]:
    """Return path parameters defined on an operation."""
    parameters = operation.get("parameters", [])
    return [
        parameter
        for parameter in parameters
        if parameter.get("in") == "path"
    ]


def generate_path_param_value(parameter: dict, spec: dict) -> str:
    """Generate a sample value for a path parameter."""
    schema = parameter.get("schema", {})

    if "$ref" in schema:
        schema = resolve_ref(schema["$ref"], spec)

    if "example" in parameter:
        return str(parameter["example"])

    if "example" in schema:
        return str(schema["example"])

    if "default" in schema:
        return str(schema["default"])

    if "enum" in schema and schema["enum"]:
        return str(schema["enum"][0])

    param_name = parameter.get("name", "value")
    param_name_lower = param_name.lower()
    schema_type = schema.get("type")

    if schema_type == "integer":
        minimum = schema.get("minimum")
        if minimum is not None:
            return str(minimum)
        return "1"

    if schema_type == "number":
        minimum = schema.get("minimum")
        if minimum is not None:
            return str(minimum)
        return "1"

    if schema_type == "boolean":
        return "true"

    if schema_type == "string":
        if "format" in schema:
            schema_format = schema["format"]

            if schema_format == "uuid":
                return "123e4567-e89b-12d3-a456-426614174000"

            if schema_format == "date":
                return "2024-01-01"

            if schema_format == "date-time":
                return "2024-01-01T00:00:00Z"

        if param_name_lower.endswith("id") or param_name_lower == "id":
            return "1"

        if "slug" in param_name_lower:
            return "example-slug"

        if "username" in param_name_lower:
            return "example-user"

        if "email" in param_name_lower:
            return "user@example.com"

        if "name" in param_name_lower:
            return "example-name"

        if "status" in param_name_lower:
            return "active"

        if "path" in param_name_lower:
            return "example-path"

        return f"example-{param_name}"

    return f"example-{param_name}"


def replace_path_params(path: str, operation: dict, spec: dict) -> str:
    """Replace OpenAPI path params with generated sample values."""
    result = path
    path_parameters = get_path_parameters(operation)

    for parameter in path_parameters:
        param_name = parameter.get("name")
        if not param_name:
            continue

        placeholder = "{" + param_name + "}"
        sample_value = generate_path_param_value(parameter, spec)
        result = result.replace(placeholder, sample_value)

    return result


def get_query_parameters(operation: dict) -> list[dict]:
    """Return query parameters defined on an operation."""
    parameters = operation.get("parameters", [])
    return [
        parameter
        for parameter in parameters
        if parameter.get("in") == "query"
    ]


def build_headers_code(
    auth_header_name: str | None,
    auth_token_env: str | None,
    auth_scheme: str | None,
) -> str | None:
    """Return Python source code for the HEADERS constant, if auth is configured."""
    if not auth_header_name or not auth_token_env:
        return None

    if auth_scheme:
        return (
            "HEADERS = {\n"
            f'    "{auth_header_name}": f"{auth_scheme} {{os.environ[\'{auth_token_env}\']}}"\n'
            "}"
        )

    return (
        "HEADERS = {\n"
        f'    "{auth_header_name}": os.environ["{auth_token_env}"]\n'
        "}"
    )


def build_request_call(
    method_lower: str,
    request_path: str,
    request_body: object | None,
    query_params: dict | None,
    include_headers: bool,
) -> str:
    """Build a requests call line for a generated test."""
    args = [f'f"{{BASE_URL}}{request_path}"']

    if query_params:
        args.append(f"params={query_params}")

    if request_body is not None and method_lower in {"post", "put", "patch"}:
        args.append("json=payload")

    if include_headers:
        args.append("headers=HEADERS")

    return f"response = requests.{method_lower}({', '.join(args)})"


def format_python_literal(value: object) -> str:
    """Convert a Python value into nicely formatted Python source code."""
    return repr(value)


def generate_property_sample_value(prop_name: str, schema: dict, spec: dict) -> object:
    """Generate a more realistic sample value for an object property."""
    if "$ref" in schema:
        resolved_schema = resolve_ref(schema["$ref"], spec)
        return generate_property_sample_value(prop_name, resolved_schema, spec)

    if "example" in schema:
        return schema["example"]

    if "default" in schema:
        return schema["default"]

    if "enum" in schema and schema["enum"]:
        return schema["enum"][0]

    prop_name_lower = prop_name.lower()
    schema_type = schema.get("type")
    schema_format = schema.get("format")

    if schema_type == "string":
        if schema_format == "email" or "email" in prop_name_lower:
            return "user@example.com"

        if schema_format == "uuid" or prop_name_lower.endswith("uuid"):
            return "123e4567-e89b-12d3-a456-426614174000"

        if schema_format == "date":
            return "2024-01-01"

        if schema_format == "date-time":
            return "2024-01-01T00:00:00Z"

        if schema_format == "uri" or "url" in prop_name_lower or "uri" in prop_name_lower:
            return "https://example.com"

        if schema_format == "password" or "password" in prop_name_lower:
            return "example-password"

        if prop_name_lower in {"first_name", "firstname"}:
            return "John"

        if prop_name_lower in {"last_name", "lastname"}:
            return "Doe"

        if prop_name_lower == "name":
            return "example-name"

        if "username" in prop_name_lower:
            return "example-user"

        if "phone" in prop_name_lower:
            return "555-123-4567"

        if "status" in prop_name_lower:
            return "active"

        if "description" in prop_name_lower:
            return "Example description"

        if "title" in prop_name_lower:
            return "Example title"

    return generate_sample_value(schema, spec)


def generate_sample_value(schema: dict, spec: dict) -> object:
    """Generate a simple sample value from a schema."""
    if "$ref" in schema:
        resolved_schema = resolve_ref(schema["$ref"], spec)
        return generate_sample_value(resolved_schema, spec)

    if "example" in schema:
        return schema["example"]

    if "default" in schema:
        return schema["default"]

    if "enum" in schema and schema["enum"]:
        return schema["enum"][0]

    schema_type = schema.get("type")
    schema_format = schema.get("format")

    if schema_type == "string":
        if schema_format == "email":
            return "user@example.com"

        if schema_format == "uuid":
            return "123e4567-e89b-12d3-a456-426614174000"

        if schema_format == "date":
            return "2024-01-01"

        if schema_format == "date-time":
            return "2024-01-01T00:00:00Z"

        if schema_format == "uri":
            return "https://example.com"

        if schema_format == "hostname":
            return "example.com"

        if schema_format == "ipv4":
            return "192.168.1.1"

        if schema_format == "ipv6":
            return "2001:db8::1"

        if schema_format == "password":
            return "example-password"

        return "string"

    if schema_type == "integer":
        minimum = schema.get("minimum")
        if minimum is not None:
            return minimum
        return 0

    if schema_type == "number":
        minimum = schema.get("minimum")
        if minimum is not None:
            return minimum
        return 0

    if schema_type == "boolean":
        return True

    if schema_type == "array":
        items_schema = schema.get("items", {})
        return [generate_sample_value(items_schema, spec)]

    if schema_type == "object":
        properties = schema.get("properties", {})
        required_fields = set(schema.get("required", []))

        result = {}

        for prop_name, prop_schema in properties.items():
            if prop_name in required_fields:
                result[prop_name] = generate_property_sample_value(
                    prop_name,
                    prop_schema,
                    spec,
                )

        for prop_name, prop_schema in properties.items():
            if prop_name not in result:
                result[prop_name] = generate_property_sample_value(
                    prop_name,
                    prop_schema,
                    spec,
                )

        return result

    return "string"


def get_json_request_body(operation: dict, spec: dict) -> dict | list | str | int | bool | None:
    """Extract a sample JSON request body from an OpenAPI operation, if present."""
    request_body = operation.get("requestBody", {})
    content = request_body.get("content", {})
    json_content = content.get("application/json", {})
    schema = json_content.get("schema")

    if not schema:
        return None

    return generate_sample_value(schema, spec)


def get_schema_from_operation(operation: dict, spec: dict) -> dict | None:
    """Get the resolved JSON schema for an operation request body, if present."""
    request_body = operation.get("requestBody", {})
    content = request_body.get("content", {})
    json_content = content.get("application/json", {})
    schema = json_content.get("schema")

    if not schema:
        return None

    if "$ref" in schema:
        return resolve_ref(schema["$ref"], spec)

    return schema


def get_success_status_code(operation: dict) -> str | None:
    """Return the first documented 2xx response code for an operation."""
    responses = operation.get("responses", {})

    success_codes = [code for code in responses if code.startswith("2")]
    if not success_codes:
        return None

    return sorted(success_codes)[0]


def get_error_status_code(operation: dict) -> str | None:
    """Return the preferred documented 4xx response code for negative tests."""
    responses = operation.get("responses", {})

    if "400" in responses:
        return "400"

    if "422" in responses:
        return "422"

    error_codes = [code for code in responses if code.startswith("4")]
    if not error_codes:
        return None

    return sorted(error_codes)[0]


def get_response_schema(operation: dict, spec: dict) -> dict | None:
    """Return the fully dereferenced JSON schema for the documented success response, if defined."""
    responses = operation.get("responses", {})
    success_code = get_success_status_code(operation)

    if not success_code:
        return None

    success_response = responses.get(success_code, {})
    content = success_response.get("content", {})
    json_content = content.get("application/json", {})
    schema = json_content.get("schema")

    if not schema:
        return None

    return dereference_schema(schema, spec)


def generate_missing_required_payloads(schema: dict, spec: dict) -> list[tuple[str, object]]:
    """
    Generate payloads with one required field removed at a time.

    Returns:
        list of (field_name, payload)
    """
    if "$ref" in schema:
        schema = resolve_ref(schema["$ref"], spec)

    if schema.get("type") != "object":
        return []

    full_payload = generate_sample_value(schema, spec)
    if not isinstance(full_payload, dict):
        return []

    required_fields = schema.get("required", [])
    results = []

    for field_name in required_fields:
        if field_name in full_payload:
            invalid_payload = dict(full_payload)
            invalid_payload.pop(field_name, None)
            results.append((field_name, invalid_payload))

    return results


def generate_invalid_enum_payloads(schema: dict, spec: dict) -> list[tuple[str, object]]:
    """
    Generate payloads with invalid enum values for top-level object properties.

    Returns:
        list of (field_name, payload)
    """
    if "$ref" in schema:
        schema = resolve_ref(schema["$ref"], spec)

    if schema.get("type") != "object":
        return []

    full_payload = generate_sample_value(schema, spec)
    if not isinstance(full_payload, dict):
        return []

    properties = schema.get("properties", {})
    results = []

    for field_name, field_schema in properties.items():
        if "$ref" in field_schema:
            field_schema = resolve_ref(field_schema["$ref"], spec)

        if "enum" in field_schema and field_name in full_payload:
            invalid_payload = dict(full_payload)
            invalid_payload[field_name] = "invalid_enum_value"
            results.append((field_name, invalid_payload))

    return results


def generate_test_function(
    method: str,
    path: str,
    operation: dict,
    spec: dict,
    include_headers: bool = False,
) -> str:
    """Generate one starter pytest test function."""
    safe_name = sanitize_path_for_name(path)
    method_lower = method.lower()
    request_path = replace_path_params(path, operation, spec)

    request_body = get_json_request_body(operation, spec)
    query_params = generate_query_params(operation, spec)
    response_schema = get_response_schema(operation, spec)
    success_status_code = get_success_status_code(operation)

    lines = [f"def test_{method_lower}_{safe_name}():"]

    if request_body is not None and method_lower in {"post", "put", "patch"}:
        body_text = format_python_literal(request_body)
        lines.append(f"    payload = {body_text}")
        request_call = build_request_call(
            method_lower,
            request_path,
            request_body,
            query_params,
            include_headers,
        )
        lines.append(f"    {request_call}")
    else:
        request_call = build_request_call(
            method_lower,
            request_path,
            None,
            query_params,
            include_headers,
        )
        lines.append(f"    {request_call}")

    if success_status_code is not None:
        lines.append(f"    assert response.status_code == {success_status_code}")
    else:
        lines.append("    assert response.status_code < 500")

    if response_schema:
        schema_text = format_python_literal(response_schema)
        lines.append('    content_type = response.headers.get("Content-Type", "")')
        lines.append('    assert "application/json" in content_type')
        lines.append("    data = response.json()")
        lines.append(f"    schema = {schema_text}")
        lines.append("    jsonschema.validate(data, schema)")

    lines.append("")

    return "\n".join(lines)


def generate_negative_test_functions(
    method: str,
    path: str,
    operation: dict,
    spec: dict,
    include_headers: bool = False,
) -> list[str]:
    """Generate negative tests for missing required fields and invalid enum values."""
    method_lower = method.lower()

    if method_lower not in {"post", "put", "patch"}:
        return []

    schema = get_schema_from_operation(operation, spec)
    if not schema:
        return []

    safe_name = sanitize_path_for_name(path)
    request_path = replace_path_params(path, operation, spec)
    error_status_code = get_error_status_code(operation)
    test_functions = []

    if error_status_code is not None:
        error_assertion = f"assert response.status_code == {error_status_code}"
    else:
        error_assertion = "assert response.status_code >= 400"

    for field_name, payload in generate_missing_required_payloads(schema, spec):
        body_text = format_python_literal(payload)
        request_call = build_request_call(
            method_lower,
            request_path,
            payload,
            None,
            include_headers,
        )
        test_functions.append(
            f'''def test_{method_lower}_{safe_name}_missing_{field_name}():
    payload = {body_text}
    {request_call}
    {error_assertion}
'''
        )

    for field_name, payload in generate_invalid_enum_payloads(schema, spec):
        body_text = format_python_literal(payload)
        request_call = build_request_call(
            method_lower,
            request_path,
            payload,
            None,
            include_headers,
        )
        test_functions.append(
            f'''def test_{method_lower}_{safe_name}_invalid_{field_name}_enum():
    payload = {body_text}
    {request_call}
    {error_assertion}
'''
        )

    return test_functions


def generate_test_file(
    endpoints: list[tuple[str, str, dict]],
    spec: dict,
    base_url: str = "http://localhost:8000",
    auth_header_name: str | None = None,
    auth_token_env: str | None = None,
    auth_scheme: str | None = None,
) -> str:
    """Generate the full contents of the output test file."""
    headers_code = build_headers_code(
        auth_header_name,
        auth_token_env,
        auth_scheme,
    )
    include_headers = headers_code is not None

    lines = [
        "import requests",
        "import jsonschema",
    ]

    if include_headers:
        lines.append("import os")

    lines.extend([
        "",
        f'BASE_URL = "{base_url}"',
    ])

    if include_headers:
        lines.extend([
            "",
            "# Set this environment variable before running the generated tests.",
            headers_code,
        ])

    lines.extend([
        "",
        "",
    ])

    for method, path, operation in endpoints:
        lines.append(
            generate_test_function(
                method,
                path,
                operation,
                spec,
                include_headers=include_headers,
            )
        )
        lines.append("")

        negative_tests = generate_negative_test_functions(
            method,
            path,
            operation,
            spec,
            include_headers=include_headers,
        )
        for test_function in negative_tests:
            lines.append(test_function)
            lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def generate_query_params(operation: dict, spec: dict) -> dict:
    """Generate query parameters for an operation."""
    params = {}

    for parameter in get_query_parameters(operation):
        name = parameter.get("name")
        if not name:
            continue

        schema = parameter.get("schema", {})

        if "$ref" in schema:
            schema = resolve_ref(schema["$ref"], spec)

        if "example" in parameter:
            params[name] = parameter["example"]
            continue

        if "example" in schema:
            params[name] = schema["example"]
            continue

        schema_type = schema.get("type")

        if schema_type == "integer":
            params[name] = 1
        elif schema_type == "number":
            params[name] = 1
        elif schema_type == "boolean":
            params[name] = True
        else:
            params[name] = "example"

    return params


def write_test_file(output_path: Path, content: str) -> None:
    """Write generated test content to disk."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")