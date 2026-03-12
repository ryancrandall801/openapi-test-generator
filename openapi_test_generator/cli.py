import argparse
import json
from pathlib import Path

import yaml

from openapi_test_generator.generator import generate_test_file, write_test_file
from openapi_test_generator.parser import (
    extract_endpoints,
    get_base_url_from_spec,
    load_openapi_spec,
)


DEFAULT_CONFIG_FILENAMES = [
    "openapi-testgen.yaml",
    "openapi-testgen.yml",
    "openapi-testgen.json",
]


def load_generator_config(config_path: Path) -> dict:
    """Load generator config from YAML or JSON."""
    try:
        text = config_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return {}

    suffix = config_path.suffix.lower()

    try:
        if suffix == ".json":
            data = json.loads(text)
        else:
            data = yaml.safe_load(text)

        if not isinstance(data, dict):
            return {}

        return data

    except Exception:
        return {}


def find_default_config() -> Path | None:
    """Return the first default config file found in the current directory."""
    for filename in DEFAULT_CONFIG_FILENAMES:
        path = Path(filename)
        if path.exists():
            return path
    return None


def parse_csv_set(value: str | None, uppercase: bool = False) -> set[str] | None:
    """Parse a comma-separated value into a set."""
    if not value:
        return None

    items = []

    for item in value.split(","):
        cleaned = item.strip()

        if not cleaned:
            continue

        if uppercase:
            cleaned = cleaned.upper()

        items.append(cleaned)

    return set(items) if items else None


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate pytest API tests from an OpenAPI spec."
    )

    parser.add_argument(
        "spec",
        help="Path or URL to the OpenAPI spec (.json, .yaml, or .yml)."
    )

    parser.add_argument(
        "-o",
        "--output",
        default="generated/generated_api_tests.py",
        help="Output test file (default: generated/generated_api_tests.py)"
    )

    parser.add_argument(
        "--base-url",
        help="Base URL used in the generated tests (defaults to first OpenAPI server, then localhost)"
    )

    parser.add_argument(
        "--methods",
        help="Comma-separated HTTP methods to generate (for example: GET or GET,POST)"
    )

    parser.add_argument(
        "--tags",
        help="Comma-separated OpenAPI tags to generate (for example: Legacy or Legacy,Authentication)"
    )

    parser.add_argument(
        "--auth-header-name",
        help="Header name for auth in generated requests (for example: Authorization or X-API-Key)"
    )

    parser.add_argument(
        "--auth-token-env",
        help="Environment variable name containing the auth token or API key"
    )

    parser.add_argument(
        "--auth-scheme",
        help="Optional auth scheme prefix (for example: Bearer)"
    )

    parser.add_argument(
        "--config",
        help="Optional path to generator config file (.yaml, .yml, or .json)."
    )

    args = parser.parse_args()

    # Load config file
    config_path = Path(args.config) if args.config else find_default_config()
    config = load_generator_config(config_path) if config_path else {}

    # Methods filtering
    selected_methods = parse_csv_set(
        args.methods if args.methods is not None else config.get("methods"),
        uppercase=True,
    )

    if selected_methods is not None:
        valid_methods = {"GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"}
        invalid_methods = selected_methods - valid_methods

        if invalid_methods:
            parser.error(f"Unsupported methods: {', '.join(sorted(invalid_methods))}")

    # Tags filtering
    selected_tags = parse_csv_set(
        args.tags if args.tags is not None else config.get("tags"),
        uppercase=False,
    )

    # Auth configuration
    auth_header_name = args.auth_header_name or config.get("auth_header_name")
    auth_token_env = args.auth_token_env or config.get("auth_token_env")
    auth_scheme = args.auth_scheme or config.get("auth_scheme")

    auth_fields = [auth_header_name, auth_token_env]

    if any(auth_fields) and not all(auth_fields):
        parser.error("--auth-header-name and --auth-token-env must be provided together")

    # Load OpenAPI spec
    spec_source = args.spec
    spec = load_openapi_spec(spec_source)

    # Resolve base URL priority
    base_url = (
        args.base_url
        or config.get("base_url")
        or get_base_url_from_spec(spec, spec_source)
        or "http://localhost:8000"
    )

    # Extract endpoints
    endpoints = extract_endpoints(
        spec,
        selected_methods=selected_methods,
        selected_tags=selected_tags,
    )

    if not endpoints:
        print("No endpoints found.")
        return

    # Generate test file
    output = generate_test_file(
        endpoints,
        spec,
        base_url,
        auth_header_name=auth_header_name,
        auth_token_env=auth_token_env,
        auth_scheme=auth_scheme,
    )

    output_path = Path(args.output)
    write_test_file(output_path, output)

    test_count = output.count("def test_")

    print(f"Generated {output_path.resolve()} with {test_count} test(s).")


if __name__ == "__main__":
    main()