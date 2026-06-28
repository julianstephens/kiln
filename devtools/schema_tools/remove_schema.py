import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

NAME_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
CONTRACT_PATH_PATTERN = re.compile(
    r"^[a-z0-9]+(?:-[a-z0-9]+)*(?:/[a-z0-9]+(?:-[a-z0-9]+)*)*$"
)


class SchemaRemovalError(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


def load_json(path: Path) -> dict[str, Any]:
    try:
        with path.open(encoding="utf-8") as file:
            value = json.load(file)
    except FileNotFoundError as exc:
        raise SchemaRemovalError(message=f"file does not exist: {path}") from exc
    except json.JSONDecodeError as exc:
        raise SchemaRemovalError(
            message=f"{path}:{exc.lineno}:{exc.colno}: invalid JSON: {exc.msg}"
        ) from exc

    if not isinstance(value, dict):
        raise SchemaRemovalError(message=f"{path}: expected a JSON object")

    return value


def write_json(path: Path, value: Any) -> None:
    path.write_text(
        json.dumps(value, indent=4) + "\n",
        encoding="utf-8",
    )


def validate_name(value: str, *, field: str) -> None:
    if not NAME_PATTERN.fullmatch(value):
        raise SchemaRemovalError(
            message=f"{field} must use lowercase kebab-case: {value!r}"
        )


def validate_contract_path(value: str) -> None:
    if not CONTRACT_PATH_PATTERN.fullmatch(value):
        raise SchemaRemovalError(
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


def fixture_prefix(*, domain: str, contract: str) -> str:
    return f"{domain}-{fixture_contract_name(contract)}-"


def remove_manifest_entry(
    manifest: dict[str, Any],
    *,
    key: str,
    force: bool,
) -> bool:
    schemas = manifest.get("schemas")
    if not isinstance(schemas, list):
        raise SchemaRemovalError(message="manifest.json: schemas must be an array")

    entrypoints = manifest.get("entrypoints")
    if entrypoints is not None and not isinstance(entrypoints, list):
        raise SchemaRemovalError(message="manifest.json: entrypoints must be an array")

    removed = False

    if key in schemas:
        schemas.remove(key)
        removed = True
    elif not force:
        raise SchemaRemovalError(message=f"manifest.json: schema is not declared: {key}")

    if isinstance(entrypoints, list) and key in entrypoints:
        entrypoints.remove(key)
        removed = True

    return removed


def remove_file(path: Path, *, force: bool) -> bool:
    if not path.exists():
        if force:
            return False
        raise SchemaRemovalError(message=f"file does not exist: {path}")

    if not path.is_file():
        raise SchemaRemovalError(message=f"expected a file: {path}")

    path.unlink()
    return True


def remove_fixtures(
    schema_root: Path,
    *,
    domain: str,
    contract: str,
    major: int,
) -> list[Path]:
    removed: list[Path] = []
    prefix = fixture_prefix(domain=domain, contract=contract)

    for fixture_kind in ("valid", "invalid"):
        fixture_dir = schema_root / "fixtures" / fixture_kind / f"v{major}"
        if not fixture_dir.exists():
            continue

        for fixture in sorted(fixture_dir.glob(f"{prefix}*.json")):
            if fixture.is_file():
                fixture.unlink()
                removed.append(fixture)

    return removed


def remove_empty_schema_dirs(
    schema_path_to_remove: Path,
    *,
    schema_root: Path,
) -> list[Path]:
    removed: list[Path] = []
    directory = schema_path_to_remove.parent

    while directory != schema_root and schema_root in directory.parents:
        try:
            directory.rmdir()
        except OSError:
            break

        removed.append(directory)
        directory = directory.parent

    return removed


def remove_schema(args: argparse.Namespace) -> None:
    schema_root = args.schema_root.resolve()
    manifest_path = schema_root / "manifest.json"
    manifest = load_json(manifest_path)

    major = manifest.get("compatibility_major")
    if not isinstance(major, int) or isinstance(major, bool) or major < 1:
        raise SchemaRemovalError(
            message="manifest.json: compatibility_major must be a positive integer"
        )

    validate_name(args.domain, field="domain")
    validate_contract_path(args.contract)

    key = schema_key(args.domain, args.contract)
    target = schema_path(
        schema_root,
        domain=args.domain,
        contract=args.contract,
        major=major,
    )

    changed_manifest = remove_manifest_entry(manifest, key=key, force=args.force)
    removed: list[Path] = []

    if remove_file(target, force=args.force):
        removed.append(target)

    if not args.keep_fixtures:
        removed.extend(
            remove_fixtures(
                schema_root,
                domain=args.domain,
                contract=args.contract,
                major=major,
            )
        )

    removed.extend(remove_empty_schema_dirs(target, schema_root=schema_root))

    if changed_manifest:
        write_json(manifest_path, manifest)

    print(f"Removed schema {key}")
    print(f"- {manifest_path.relative_to(schema_root.parent)}")

    for path in removed:
        print(f"- {path.relative_to(schema_root.parent)}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Remove a Kiln JSON Schema file and unregister it from "
            "schemas/manifest.json."
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
        help="Path containing manifest.json. Defaults to the schemas directory.",
    )
    parser.add_argument(
        "--keep-fixtures",
        action="store_true",
        help="Keep matching valid and invalid fixtures.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Do not fail when the schema is already absent.",
    )

    return parser.parse_args()


def main() -> int:
    args = parse_args()

    try:
        remove_schema(args)
    except SchemaRemovalError as exc:
        print(f"schema removal failed: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
