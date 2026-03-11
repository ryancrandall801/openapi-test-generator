import json
import sys
from pathlib import Path

import yaml


HTTP_METHODS = {"get", "post", "put", "delete", "patch", "options", "head"}


def load_openapi_spec(file_path: Path) -> dict:
    """Load an OpenAPI spec from a JSON or YAML file."""
    try:
        with file_path.open("r", encoding="utf-8") as f:
            suffix = file_path.suffix.lower()

            if suffix == ".json":
                return json.load(f)

            if suffix in {".yaml", ".yml"}:
                data = yaml.safe_load(f)
                if not isinstance(data, dict):
                    print(f"Error: YAML file did not contain a valid OpenAPI object: {file_path}")
                    sys.exit(1)
                return data

            print(
                f"Error: unsupported file type '{file_path.suffix}'. "
                "Use .json, .yaml, or .yml"
            )
            sys.exit(1)

    except FileNotFoundError:
        print(f"Error: file not found: {file_path}")
        sys.exit(1)

    except json.JSONDecodeError as e:
        print(f"Error: invalid JSON in {file_path}")
        print(f"Details: {e}")
        sys.exit(1)

    except yaml.YAMLError as e:
        print(f"Error: invalid YAML in {file_path}")
        print(f"Details: {e}")
        sys.exit(1)


def extract_endpoints(
    spec: dict,
    selected_methods: set[str] | None = None,
) -> list[tuple[str, str, dict]]:
    """Return a list of (METHOD, PATH, OPERATION) tuples from the OpenAPI spec."""
    endpoints = []
    paths = spec.get("paths", {})

    for path, path_item in paths.items():
        if not isinstance(path_item, dict):
            continue

        for method, operation in path_item.items():
            if method.lower() in HTTP_METHODS:
                endpoints.append((method.upper(), path, operation))

    return endpoints