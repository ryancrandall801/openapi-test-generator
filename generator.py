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
        return {
            prop_name: generate_sample_value(prop_schema, spec)
            for prop_name, prop_schema in properties.items()
        }

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


def format_python_literal(value: object) -> str:
    """Convert a Python value into nicely formatted Python source code."""
    return repr(value)


def generate_test_function(method: str, path: str, operation: dict, spec: dict) -> str:
    """Generate one starter pytest test function."""
    safe_name = sanitize_path_for_name(path)
    method_lower = method.lower()
    request_path = replace_path_params(path)
    request_body = get_json_request_body(operation, spec)

    if request_body is not None and method_lower in {"post", "put", "patch"}:
        body_text = format_python_literal(request_body)
        return f'''def test_{method_lower}_{safe_name}():
    payload = {body_text}
    response = requests.{method_lower}(f"{{BASE_URL}}{request_path}", json=payload)
    assert response.status_code < 500
'''
    return f'''def test_{method_lower}_{safe_name}():
    response = requests.{method_lower}(f"{{BASE_URL}}{request_path}")
    assert response.status_code < 500
'''


def generate_test_file(endpoints: list[tuple[str, str, dict]], spec: dict) -> str:
    """Generate the full contents of test_api.py."""
    lines = [
        "import requests",
        "",
        'BASE_URL = "http://localhost:8000"',
        "",
        "",
    ]

    for method, path, operation in endpoints:
        lines.append(generate_test_function(method, path, operation, spec))
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def write_test_file(output_path: Path, content: str) -> None:
    """Write generated test content to disk."""
    output_path.write_text(content, encoding="utf-8")