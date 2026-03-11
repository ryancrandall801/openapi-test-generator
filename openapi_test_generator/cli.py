import argparse
from pathlib import Path

from openapi_test_generator.generator import generate_test_file, write_test_file
from openapi_test_generator.parser import extract_endpoints, load_openapi_spec


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
        default="http://localhost:8000",
        help="Base URL used in the generated tests (default: http://localhost:8000)"
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

    args = parser.parse_args()

    auth_fields = [args.auth_header_name, args.auth_token_env]
    if any(auth_fields) and not all(auth_fields):
        parser.error("--auth-header-name and --auth-token-env must be provided together")

    selected_methods = None
    if args.methods:
        selected_methods = {
            method.strip().upper()
            for method in args.methods.split(",")
            if method.strip()
        }

        valid_methods = {"GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"}
        invalid_methods = selected_methods - valid_methods
        if invalid_methods:
            parser.error(f"Unsupported methods: {', '.join(sorted(invalid_methods))}")

    selected_tags = None
    if args.tags:
        selected_tags = {
            tag.strip()
            for tag in args.tags.split(",")
            if tag.strip()
        }

    spec_source = args.spec
    spec = load_openapi_spec(spec_source)
    endpoints = extract_endpoints(
        spec,
        selected_methods=selected_methods,
        selected_tags=selected_tags,
    )

    if not endpoints:
        print("No endpoints found.")
        return

    output = generate_test_file(
        endpoints,
        spec,
        args.base_url,
        auth_header_name=args.auth_header_name,
        auth_token_env=args.auth_token_env,
        auth_scheme=args.auth_scheme,
    )

    output_path = Path(args.output)
    write_test_file(output_path, output)

    test_count = output.count("def test_")
    print(f"Generated {output_path.resolve()} with {test_count} test(s).")


if __name__ == "__main__":
    main()