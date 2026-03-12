import json
import sys
from pathlib import Path
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen

import yaml


HTTP_METHODS = {"get", "post", "put", "delete", "patch", "options", "head"}


def is_url(source: str) -> bool:
    """Return True if the source looks like an HTTP(S) URL."""
    parsed = urlparse(source)
    return parsed.scheme in {"http", "https"}


def parse_openapi_text(text: str, source_name: str) -> dict:
    """Parse OpenAPI text as JSON or YAML."""
    source_lower = source_name.lower()

    try:
        if source_lower.endswith(".json"):
            data = json.loads(text)
        elif source_lower.endswith((".yaml", ".yml")):
            data = yaml.safe_load(text)
        else:
            try:
                data = json.loads(text)
            except json.JSONDecodeError:
                data = yaml.safe_load(text)

        if not isinstance(data, dict):
            print(f"Error: OpenAPI source did not contain a valid object: {source_name}")
            sys.exit(1)

        return data

    except json.JSONDecodeError as e:
        print(f"Error: invalid JSON in {source_name}")
        print(f"Details: {e}")
        sys.exit(1)

    except yaml.YAMLError as e:
        print(f"Error: invalid YAML in {source_name}")
        print(f"Details: {e}")
        sys.exit(1)


def load_openapi_spec(source: str | Path) -> dict:
    """Load an OpenAPI spec from a local file path or URL."""
    source_str = str(source)

    if is_url(source_str):
        try:
            request = Request(
                source_str,
                headers={
                    "User-Agent": "openapi-testgen/0.1.0",
                    "Accept": "application/json, application/yaml, text/yaml, */*",
                },
            )

            with urlopen(request) as response:
                text = response.read().decode("utf-8")

            return parse_openapi_text(text, source_str)

        except Exception as e:
            print(f"Error: could not fetch OpenAPI spec from URL: {source_str}")
            print(f"Details: {e}")
            sys.exit(1)

    file_path = Path(source_str)

    try:
        text = file_path.read_text(encoding="utf-8")
        return parse_openapi_text(text, file_path.name)

    except FileNotFoundError:
        print(f"Error: file not found: {file_path}")
        sys.exit(1)

    except OSError as e:
        print(f"Error: could not read file: {file_path}")
        print(f"Details: {e}")
        sys.exit(1)


def extract_endpoints(
    spec: dict,
    selected_methods: set[str] | None = None,
    selected_tags: set[str] | None = None,
) -> list[tuple[str, str, dict]]:
    """Return a list of (METHOD, PATH, OPERATION) tuples from the OpenAPI spec."""
    endpoints = []
    paths = spec.get("paths", {})

    for path, path_item in paths.items():
        if not isinstance(path_item, dict):
            continue

        path_level_parameters = path_item.get("parameters", [])

        for method, operation in path_item.items():
            if method.lower() not in HTTP_METHODS:
                continue

            method_upper = method.upper()

            if selected_methods is not None and method_upper not in selected_methods:
                continue

            if not isinstance(operation, dict):
                continue

            operation_tags = set(operation.get("tags", []))
            if selected_tags is not None and not (operation_tags & selected_tags):
                continue

            merged_operation = dict(operation)
            operation_parameters = operation.get("parameters", [])
            merged_operation["parameters"] = path_level_parameters + operation_parameters

            endpoints.append((method_upper, path, merged_operation))

    return endpoints


def get_base_url_from_spec(spec: dict, spec_source: str | None = None) -> str | None:
    """Return the first server URL from the OpenAPI spec, resolving relative URLs when possible."""
    servers = spec.get("servers", [])

    if not isinstance(servers, list) or not servers:
        return None

    first_server = servers[0]

    if not isinstance(first_server, dict):
        return None

    url = first_server.get("url")

    if not isinstance(url, str) or not url.strip():
        return None

    url = url.strip()
    parsed = urlparse(url)

    if parsed.scheme in {"http", "https"}:
        return url

    if spec_source:
        source_parsed = urlparse(str(spec_source))

        if source_parsed.scheme in {"http", "https"}:
            return urljoin(str(spec_source), url)

    return url