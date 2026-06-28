import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

SCHEMA_BASE_URL = "https://kiln.cyborgdev.cloud/schemas"
NAME_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
CONTRACT_PATH_PATTERN = re.compile(
    r"^[a-z0-9]+(?:-[a-z0-9]+)*(?:/[a-z0-9]+(?:-[a-z0-9]+)*)*$"
)


class SchemaCreationError(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


def load_json(path: Path) -> dict[str, Any]:
    try:
        with path.open(encoding="utf-8") as file:
            value = json.load(file)
    except FileNotFoundError as exc:
        raise SchemaCreationError(message=f"file does not exist: {path}") from exc
    except json.JSONDecodeError as exc:
        raise SchemaCreationError(
            message=f"{path}:{exc.lineno}:{exc.colno}: invalid JSON: {exc.msg}"
        ) from exc

    if not isinstance(value, dict):
        raise SchemaCreationError(message=f"{path}: expected a JSON object")

    return value


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=4) + "\n",
        encoding="utf-8",
    )


def validate_name(value: str, *, field: str) -> None:
    if not NAME_PATTERN.fullmatch(value):
        raise SchemaCreationError(
            message=f"{field} must use lowercase kebab-case: {value!r}"
        )


def validate_contract_path(value: str) -> None:
    if not CONTRACT_PATH_PATTERN.fullmatch(value):
        raise SchemaCreationError(
            message=(
                "contract must use lowercase kebab-case path segments "
                f"separated by '/': {value!r}"
            )
        )


def schema_key(domain: str, contract: str) -> str:
    return f"{domain}/{contract}"


def contract_path(contract: str) -> Path:
    parts = contract.split("/")
    return Path(*parts[:-1]) / f"{parts[-1]}.schema.json"


def fixture_contract_name(contract: str) -> str:
    return contract.replace("/", "-")


def schema_path(
    schema_root: Path,
    *,
    domain: str,
    contract: str,
    major: int,
) -> Path:
    return schema_root / domain / f"v{major}" / contract_path(contract)


def fixture_path(
    schema_root: Path,
    *,
    fixture_kind: str,
    domain: str,
    contract: str,
    case: str,
    major: int,
) -> Path:
    return (
        schema_root
        / "fixtures"
        / fixture_kind
        / f"v{major}"
        / f"{domain}-{fixture_contract_name(contract)}-{case}.json"
    )


def schema_document(
    *,
    domain: str,
    contract: str,
    major: int,
    schema_set_version: str,
    title: str,
) -> dict[str, Any]:
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": (f"{SCHEMA_BASE_URL}/" f"{domain}/v{major}/{contract}.schema.json"),
        "x-kiln-schema-release": schema_set_version,
        "title": title,
        "type": "object",
        "additionalProperties": False,
        "required": [],
        "properties": {},
    }


def add_to_manifest(
    manifest: dict[str, Any],
    *,
    key: str,
    entrypoint: bool,
) -> None:
    schemas = manifest.get("schemas")
    if not isinstance(schemas, list):
        raise SchemaCreationError(message="manifest.json: schemas must be an array")

    if key not in schemas:
        schemas.append(key)
        schemas.sort()

    if entrypoint:
        entrypoints = manifest.setdefault("entrypoints", [])

        if not isinstance(entrypoints, list):
            raise SchemaCreationError(
                message="manifest.json: entrypoints must be an array"
            )

        if key not in entrypoints:
            entrypoints.append(key)
            entrypoints.sort()


def create_fixture(
    path: Path,
    *,
    contents: dict[str, Any],
    force: bool,
) -> None:
    if path.exists() and not force:
        raise SchemaCreationError(message=f"fixture already exists: {path}")

    write_json(path, contents)


def create_schema(args: argparse.Namespace) -> None:
    schema_root = args.schema_root.resolve()
    manifest_path = schema_root / "manifest.json"
    manifest = load_json(manifest_path)

    major = manifest.get("compatibility_major")
    if not isinstance(major, int) or isinstance(major, bool) or major < 1:
        raise SchemaCreationError(
            message="manifest.json: compatibility_major must be a positive integer"
        )

    schema_set_version = manifest.get("schema_set_version")
    if not isinstance(schema_set_version, str) or not schema_set_version:
        raise SchemaCreationError(
            message="manifest.json: schema_set_version must be a non-empty string"
        )

    validate_name(args.domain, field="domain")
    validate_contract_path(args.contract)

    if args.valid_case:
        validate_name(args.valid_case, field="valid case")

    if args.invalid_case:
        validate_name(args.invalid_case, field="invalid case")

    key = schema_key(args.domain, args.contract)
    destination = schema_path(
        schema_root,
        domain=args.domain,
        contract=args.contract,
        major=major,
    )

    if destination.exists() and not args.force:
        raise SchemaCreationError(message=f"schema already exists: {destination}")

    contract_title = args.contract.replace("/", " ").replace("-", " ")
    title = args.title or f"Kiln {args.domain} {contract_title}"

    document = schema_document(
        domain=args.domain,
        contract=args.contract,
        major=major,
        schema_set_version=schema_set_version,
        title=title,
    )

    write_json(destination, document)

    add_to_manifest(
        manifest,
        key=key,
        entrypoint=args.entrypoint,
    )
    write_json(manifest_path, manifest)

    created = [destination, manifest_path]

    if args.valid_case:
        valid_path = fixture_path(
            schema_root,
            fixture_kind="valid",
            domain=args.domain,
            contract=args.contract,
            case=args.valid_case,
            major=major,
        )
        create_fixture(
            valid_path,
            contents={},
            force=args.force,
        )
        created.append(valid_path)

    if args.invalid_case:
        invalid_path = fixture_path(
            schema_root,
            fixture_kind="invalid",
            domain=args.domain,
            contract=args.contract,
            case=args.invalid_case,
            major=major,
        )
        create_fixture(
            invalid_path,
            contents={},
            force=args.force,
        )
        created.append(invalid_path)

    print(f"Created schema {key}")

    for path in created:
        print(f"- {path.relative_to(schema_root.parent)}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Create a Kiln JSON Schema file and register it "
            "in schemas/manifest.json."
        )
    )

    parser.add_argument(
        "domain",
        help="Schema domain in lowercase kebab-case.",
    )
    parser.add_argument(
        "contract",
        help=(
            "Contract name or nested contract path using lowercase "
            "kebab-case path segments, such as payload/run-created."
        ),
    )
    parser.add_argument(
        "--schema-root",
        type=Path,
        default=Path(__file__).resolve().parents[2] / "schemas",
        help=("Path containing manifest.json. Defaults to " "the schemas directory."),
    )
    parser.add_argument(
        "--title",
        help="Override the generated schema title.",
    )
    parser.add_argument(
        "--entrypoint",
        action="store_true",
        help="Add the schema to manifest entrypoints.",
    )
    parser.add_argument(
        "--valid-case",
        metavar="CASE",
        help=(
            "Create an empty valid fixture named "
            "<domain>-<flattened-contract>-<case>.json."
        ),
    )
    parser.add_argument(
        "--invalid-case",
        metavar="CASE",
        help=(
            "Create an empty invalid fixture named "
            "<domain>-<flattened-contract>-<case>.json."
        ),
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing generated files.",
    )

    return parser.parse_args()


def main() -> int:
    args = parse_args()

    try:
        create_schema(args)
    except SchemaCreationError as exc:
        print(f"schema creation failed: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
