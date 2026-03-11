import argparse
from pathlib import Path

from generator import generate_test_file, write_test_file
from parser import extract_endpoints, load_openapi_spec


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate pytest API tests from an OpenAPI spec."
    )

    parser.add_argument(
        "spec",
        help="Path to the OpenAPI spec file (.json, .yaml, or .yml)."
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

    args = parser.parse_args()

    file_path = Path(args.spec)
    spec = load_openapi_spec(file_path)
    endpoints = extract_endpoints(spec)

    if not endpoints:
        print("No endpoints found.")
        return

    output = generate_test_file(endpoints, spec)

    output_path = Path(args.output)
    write_test_file(output_path, output)

    test_count = output.count("def test_")

    print(f"Generated {output_path.resolve()} with {test_count} test(s).")


if __name__ == "__main__":
    main()