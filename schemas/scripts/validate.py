import json
import sys
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

SCHEMA_DIR = Path(__file__).resolve().parents[1]
SCHEMA_PATH = SCHEMA_DIR / "protocol.schema.json"
VALID_DIR = SCHEMA_DIR / "fixtures" / "valid"
INVALID_DIR = SCHEMA_DIR / "fixtures" / "invalid"


def load_json(path: Path) -> object:
    with path.open(encoding="utf-8") as file:
        return json.load(file)


def validate_fixture(
    validator: Draft202012Validator,
    path: Path,
    *,
    should_pass: bool,
) -> list[str]:
    instance = load_json(path)
    errors = sorted(validator.iter_errors(instance), key=lambda error: list(error.path))  # type: ignore

    if should_pass and errors:
        return [
            f"{path}: expected valid fixture, got: {error.message}" for error in errors
        ]

    if not should_pass and not errors:
        return [f"{path}: expected invalid fixture, but validation passed"]

    return []


def main() -> int:
    schema = load_json(SCHEMA_PATH)

    Draft202012Validator.check_schema(schema)  # type: ignore

    validator = Draft202012Validator(
        schema,  # type: ignore
        format_checker=FormatChecker(),
    )

    failures: list[str] = []

    for path in sorted(VALID_DIR.glob("*.json")):
        failures.extend(validate_fixture(validator, path, should_pass=True))

    for path in sorted(INVALID_DIR.glob("*.json")):
        failures.extend(validate_fixture(validator, path, should_pass=False))

    if failures:
        for failure in failures:
            print(failure, file=sys.stderr)
        return 1

    print("Schema validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
