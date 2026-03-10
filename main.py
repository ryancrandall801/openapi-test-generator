import json
import sys
from pathlib import Path


HTTP_METHODS = {"get", "post", "put", "delete", "patch", "options", "head"}


def load_openapi_spec(file_path: Path) -> dict:
    """Load an OpenAPI spec from a JSON file."""
    try:
        with file_path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: file not found: {file_path}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: invalid JSON in {file_path}")
        print(f"Details: {e}")
        sys.exit(1)


def extract_endpoints(spec: dict) -> list[tuple[str, str]]:
    """Return a list of (METHOD, PATH) tuples from the OpenAPI spec."""
    endpoints = []
    paths = spec.get("paths", {})

    for path, path_item in paths.items():
        if not isinstance(path_item, dict):
            continue

        for method in path_item:
            if method.lower() in HTTP_METHODS:
                endpoints.append((method.upper(), path))

    return endpoints


def sanitize_path_for_name(path: str) -> str:
    """
    Convert an API path into something safe for a Python test name.

    Example:
    /users/{id} -> users_id
    """
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
        result = result[:start] + "1" + result[end + 1:]
    return result


def generate_test_function(method: str, path: str) -> str:
    """Generate one starter pytest test function."""
    safe_name = sanitize_path_for_name(path)
    method_lower = method.lower()
    request_path = replace_path_params(path)

    return f'''def test_{method_lower}_{safe_name}():
    response = requests.{method_lower}(f"{{BASE_URL}}{request_path}")
    assert response.status_code < 500
'''


def generate_test_file(endpoints: list[tuple[str, str]]) -> str:
    """Generate the full contents of test_api.py."""
    lines = [
        "import requests",
        "",
        'BASE_URL = "http://localhost:8000"',
        "",
        "",
    ]

    for method, path in endpoints:
        lines.append(generate_test_function(method, path))
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def write_test_file(output_path: Path, content: str) -> None:
    """Write generated test content to disk."""
    output_path.write_text(content, encoding="utf-8")


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: python main.py <openapi_spec.json>")
        sys.exit(1)

    file_path = Path(sys.argv[1])
    spec = load_openapi_spec(file_path)
    endpoints = extract_endpoints(spec)

    if not endpoints:
        print("No endpoints found.")
        return

    output = generate_test_file(endpoints)
    output_path = Path("test_api.py")
    write_test_file(output_path, output)

    print(f"Generated {output_path} with {len(endpoints)} test(s).")


if __name__ == "__main__":
    main()