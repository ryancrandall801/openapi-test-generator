from pathlib import Path


def sanitize_path_for_name(path: str) -> str:
    """Convert an API path into something safe for a Python test name."""
    cleaned = path.strip("/")
    cleaned = cleaned.replace("/", "_")
    cleaned = cleaned.replace("{", "")
    cleaned = cleaned.replace("}", "")
    cleaned = cleaned.replace("-", "_")
    return cleaned or "root"


def replace_path_params(path: str) -> str:
    """Replace OpenAPI path params like {id} with a sample value."""
    result = path
    while "{" in result and "}" in result:
        start = result.index("{")
        end = result.index("}", start)
        result = result[:start] + "1" + result[end + 1 :]
    return result


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


def generate_sample_value(schema: dict, spec: dict) -> object:
    """Generate a simple sample value from a schema."""
    if "$ref" in schema:
        resolved_schema = resolve_ref(schema["$ref"], spec)
        return generate_sample_value(resolved_schema, spec)

    if "example" in schema:
        return schema["example"]

    if "default" in schema:
        return schema["default"]

    schema_type = schema.get("type")

    if schema_type == "string":
        return "string"

    if schema_type == "integer":
        return 0

    if schema_type == "number":
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
                result[prop_name] = generate_sample_value(prop_schema, spec)

        for prop_name, prop_schema in properties.items():
            if prop_name not in result:
                result[prop_name] = generate_sample_value(prop_schema, spec)

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
    """Return the JSON schema for the documented success response, if defined."""
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

    if "$ref" in schema:
        return resolve_ref(schema["$ref"], spec)

    return schema


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


def format_python_literal(value: object) -> str:
    """Convert a Python value into nicely formatted Python source code."""
    return repr(value)


def generate_test_function(method: str, path: str, operation: dict, spec: dict) -> str:
    """Generate one starter pytest test function."""
    safe_name = sanitize_path_for_name(path)
    method_lower = method.lower()
    request_path = replace_path_params(path)

    request_body = get_json_request_body(operation, spec)
    response_schema = get_response_schema(operation, spec)
    success_status_code = get_success_status_code(operation)

    lines = [f"def test_{method_lower}_{safe_name}():"]

    if request_body is not None and method_lower in {"post", "put", "patch"}:
        body_text = format_python_literal(request_body)
        lines.append(f"    payload = {body_text}")
        lines.append(
            f'    response = requests.{method_lower}(f"{{BASE_URL}}{request_path}", json=payload)'
        )
    else:
        lines.append(
            f'    response = requests.{method_lower}(f"{{BASE_URL}}{request_path}")'
        )

    if success_status_code is not None:
        lines.append(f"    assert response.status_code == {success_status_code}")
    else:
        lines.append("    assert response.status_code < 500")

    if response_schema:
        schema_text = format_python_literal(response_schema)
        lines.append("    data = response.json()")
        lines.append(f"    schema = {schema_text}")
        lines.append("    jsonschema.validate(data, schema)")

    lines.append("")

    return "\n".join(lines)


def generate_negative_test_functions(method: str, path: str, operation: dict, spec: dict) -> list[str]:
    """Generate negative tests for missing required fields and invalid enum values."""
    method_lower = method.lower()

    if method_lower not in {"post", "put", "patch"}:
        return []

    schema = get_schema_from_operation(operation, spec)
    if not schema:
        return []

    safe_name = sanitize_path_for_name(path)
    request_path = replace_path_params(path)
    error_status_code = get_error_status_code(operation)
    test_functions = []

    if error_status_code is not None:
        error_assertion = f"assert response.status_code == {error_status_code}"
    else:
        error_assertion = "assert response.status_code >= 400"

    for field_name, payload in generate_missing_required_payloads(schema, spec):
        body_text = format_python_literal(payload)
        test_functions.append(
            f'''def test_{method_lower}_{safe_name}_missing_{field_name}():
    payload = {body_text}
    response = requests.{method_lower}(f"{{BASE_URL}}{request_path}", json=payload)
    {error_assertion}
'''
        )

    for field_name, payload in generate_invalid_enum_payloads(schema, spec):
        body_text = format_python_literal(payload)
        test_functions.append(
            f'''def test_{method_lower}_{safe_name}_invalid_{field_name}_enum():
    payload = {body_text}
    response = requests.{method_lower}(f"{{BASE_URL}}{request_path}", json=payload)
    {error_assertion}
'''
        )

    return test_functions


def generate_test_file(
    endpoints: list[tuple[str, str, dict]],
    spec: dict,
    base_url: str = "http://localhost:8000",
) -> str:
    """Generate the full contents of the output test file."""
    lines = [
        "import requests",
        "import jsonschema",
        "",
        f'BASE_URL = "{base_url}"',
        "",
        "",
    ]

    for method, path, operation in endpoints:
        lines.append(generate_test_function(method, path, operation, spec))
        lines.append("")

        negative_tests = generate_negative_test_functions(method, path, operation, spec)
        for test_function in negative_tests:
            lines.append(test_function)
            lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def write_test_file(output_path: Path, content: str) -> None:
    """Write generated test content to disk."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")
