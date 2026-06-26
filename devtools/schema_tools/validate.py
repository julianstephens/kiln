import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urljoin, urlparse

from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import SchemaError
from referencing import Registry, Resource
from referencing.exceptions import NoSuchResource

EXPECTED_DIALECT = "https://json-schema.org/draft/2020-12/schema"


@dataclass(frozen=True)
class SchemaDefinition:
    """
    One schema declared by manifest.json.
    """

    key: str
    domain: str
    contract: str
    path: Path
    contents: dict[str, Any]

    @property
    def fixture_prefix(self) -> str:
        return f"{self.domain}-{self.contract}-"


class ValidationFailureError(Exception):
    """
    Raised for repository-level schema validation errors.
    """

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


def load_json(path: Path) -> Any:
    try:
        with path.open(encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError as exc:
        raise ValidationFailureError(message=f"file does not exist: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValidationFailureError(
            message=f"{path}:{exc.lineno}:{exc.colno}: invalid JSON: {exc.msg}"
        ) from exc
    except OSError as exc:
        raise ValidationFailureError(message=f"could not read {path}: {exc}") from exc


def require_object(value: Any, *, path: Path) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValidationFailureError(message=f"{path}: expected a JSON object")

    return value


def load_manifest(schema_root: Path) -> dict[str, Any]:
    manifest_path = schema_root / "manifest.json"
    manifest = require_object(load_json(manifest_path), path=manifest_path)

    required_fields = {
        "schema_set_version",
        "compatibility_major",
        "schemas",
    }

    missing_fields = sorted(required_fields - manifest.keys())
    if missing_fields:
        raise ValidationFailureError(
            message=f"{manifest_path}: missing required fields: "
            f"{', '.join(missing_fields)}"
        )

    schema_set_version = manifest["schema_set_version"]
    if not isinstance(schema_set_version, str) or not schema_set_version:
        raise ValidationFailureError(
            message=f"{manifest_path}: schema_set_version must be a non-empty string"
        )

    compatibility_major = manifest["compatibility_major"]
    if (
        not isinstance(compatibility_major, int)
        or isinstance(compatibility_major, bool)
        or compatibility_major < 1
    ):
        raise ValidationFailureError(
            message=f"{manifest_path}: compatibility_major must be a positive integer"
        )

    version_parts = schema_set_version.split(".")
    if len(version_parts) < 1 or not version_parts[0].isdigit():
        raise ValidationFailureError(
            message=f"{manifest_path}: schema_set_version {schema_set_version!r} "
            "is not a valid semver string"
        )

    version_major = int(version_parts[0])
    if version_major != compatibility_major:
        raise ValidationFailureError(
            message=f"{manifest_path}: schema_set_version major {version_major} "
            f"does not match compatibility_major {compatibility_major}"
        )

    schemas = manifest["schemas"]
    if not isinstance(schemas, list) or not schemas:
        raise ValidationFailureError(
            message=f"{manifest_path}: schemas must be a non-empty array"
        )

    seen: set[str] = set()

    for index, schema_key in enumerate(schemas):
        if not isinstance(schema_key, str) or not schema_key:
            raise ValidationFailureError(
                message=f"{manifest_path}: schemas[{index}] must be a non-empty string"
            )

        parts = schema_key.split("/")
        if len(parts) != 2 or not all(parts):
            raise ValidationFailureError(
                message=f"{manifest_path}: invalid schema entry {schema_key!r}; "
                "expected '<domain>/<contract>'"
            )

        if schema_key in seen:
            raise ValidationFailureError(
                message=f"{manifest_path}: duplicate schema entry: {schema_key}"
            )

        seen.add(schema_key)

    entrypoints = manifest.get("entrypoints")
    if entrypoints is not None:
        if not isinstance(entrypoints, list) or not entrypoints:
            raise ValidationFailureError(
                message=f"{manifest_path}: entrypoints must be a non-empty array"
            )

        seen_entrypoints: set[str] = set()

        for index, ep_key in enumerate(entrypoints):
            if not isinstance(ep_key, str) or not ep_key:
                raise ValidationFailureError(
                    message=(
                        f"{manifest_path}: entrypoints[{index}] must be a "
                        "non-empty string"
                    )
                )

            parts = ep_key.split("/")
            if len(parts) != 2 or not all(parts):
                raise ValidationFailureError(
                    message=f"{manifest_path}: invalid entrypoint entry {ep_key!r}; "
                    "expected '<domain>/<contract>'"
                )

            if ep_key in seen_entrypoints:
                raise ValidationFailureError(
                    message=f"{manifest_path}: duplicate entrypoint entry: {ep_key}"
                )

            seen_entrypoints.add(ep_key)

        not_in_schemas = sorted(seen_entrypoints - seen)
        if not_in_schemas:
            raise ValidationFailureError(
                message=(
                    f"{manifest_path}: entrypoints contains keys not declared in "
                    "schemas: "
                )
                + ", ".join(not_in_schemas)
            )

    return manifest


def load_schemas(
    schema_root: Path,
    manifest: dict[str, Any],
) -> list[SchemaDefinition]:
    major = manifest["compatibility_major"]
    definitions: list[SchemaDefinition] = []
    seen_ids: dict[str, Path] = {}

    for schema_key in manifest["schemas"]:
        domain, contract = schema_key.split("/", maxsplit=1)
        path = schema_root / domain / f"v{major}" / f"{contract}.schema.json"
        contents = require_object(load_json(path), path=path)

        if contents.get("$schema") != EXPECTED_DIALECT:
            print("SCHEMA", contents.get("$schema"))
            raise ValidationFailureError(
                message=f"{path}: $schema must be {EXPECTED_DIALECT!r}"
            )

        schema_release = contents.get("x-kiln-schema-release")
        expected_release = manifest["schema_set_version"]
        if schema_release != expected_release:
            raise ValidationFailureError(
                message=f"{path}: x-kiln-schema-release {schema_release!r} "
                f"does not match manifest schema_set_version {expected_release!r}"
            )

        try:
            Draft202012Validator.check_schema(contents)
        except SchemaError as exc:
            detail = exc.message or str(exc)
            raise ValidationFailureError(
                message=f"{path}: invalid Draft 2020-12 schema: {detail}"
            ) from exc

        schema_id = contents.get("$id")
        if not isinstance(schema_id, str) or not schema_id:
            raise ValidationFailureError(
                message=f"{path}: schema must define a non-empty string $id"
            )

        # Validate that the $id path encodes the correct domain, version, and
        # contract, and that the local file path is consistent with all three.
        id_path = urlparse(schema_id).path
        expected_id_path = f"/schemas/{domain}/v{major}/{contract}.schema.json"
        if id_path != expected_id_path:
            raise ValidationFailureError(
                message=f"{path}: $id path {id_path!r} does not match "
                f"expected {expected_id_path!r} for manifest key "
                f"{schema_key!r} with compatibility_major={major}"
            )

        expected_local_suffix = Path(domain) / f"v{major}" / f"{contract}.schema.json"
        try:
            actual_local_suffix = path.relative_to(schema_root)
        except ValueError:
            actual_local_suffix = path
        if actual_local_suffix != expected_local_suffix:
            raise ValidationFailureError(
                message=f"{path}: local path suffix {str(actual_local_suffix)!r} "
                f"does not match expected {str(expected_local_suffix)!r} for "
                f"manifest key {schema_key!r} with compatibility_major={major}"
            )

        previous_path = seen_ids.get(schema_id)
        if previous_path is not None:
            raise ValidationFailureError(
                message=f"{path}: duplicate $id {schema_id!r}; "
                f"already used by {previous_path}"
            )

        seen_ids[schema_id] = path

        definitions.append(
            SchemaDefinition(
                key=schema_key,
                domain=domain,
                contract=contract,
                path=path,
                contents=contents,
            )
        )

    return definitions


def build_registry(
    definitions: list[SchemaDefinition],
) -> Registry:
    registry = Registry()

    for definition in definitions:
        schema_id = definition.contents["$id"]

        try:
            resource = Resource.from_contents(definition.contents)
        except Exception as exc:
            raise ValidationFailureError(
                message=f"{definition.path}: could not create schema resource: {exc}"
            ) from exc

        registry = registry.with_resource(schema_id, resource)

    return registry


def entrypoint_definitions(
    definitions: list[SchemaDefinition],
    manifest: dict[str, Any],
) -> list[SchemaDefinition]:
    """Return the subset of definitions that are declared entrypoints.

    Falls back to all definitions when the manifest omits ``entrypoints``.
    """
    entrypoints = manifest.get("entrypoints")
    if entrypoints is None:
        return list(definitions)
    keys = set(entrypoints)
    return [d for d in definitions if d.key in keys]


def find_fixture_schema(
    fixture_path: Path,
    definitions: list[SchemaDefinition],
) -> SchemaDefinition:
    filename = fixture_path.name

    matches = [
        definition
        for definition in definitions
        if filename.startswith(definition.fixture_prefix) and filename.endswith(".json")
    ]

    if not matches:
        expected = ", ".join(
            sorted(
                f"{definition.fixture_prefix}<case>.json" for definition in definitions
            )
        )
        raise ValidationFailureError(
            message=f"{fixture_path}: filename does not match a declared schema; "
            f"expected one of: {expected}"
        )

    # Prefer the longest prefix so contracts such as `request` and
    # `request-envelope` can coexist without ambiguous fixture matching.
    matches.sort(
        key=lambda definition: len(definition.fixture_prefix),
        reverse=True,
    )

    longest_length = len(matches[0].fixture_prefix)
    longest_matches = [
        definition
        for definition in matches
        if len(definition.fixture_prefix) == longest_length
    ]

    if len(longest_matches) > 1:
        keys = ", ".join(sorted(definition.key for definition in longest_matches))
        raise ValidationFailureError(
            message=f"{fixture_path}: fixture name ambiguously matches: {keys}"
        )

    return longest_matches[0]


def format_instance_path(error: Any) -> str:
    if not error.absolute_path:
        return "$"

    parts = ["$"]

    for item in error.absolute_path:
        if isinstance(item, int):
            parts.append(f"[{item}]")
        else:
            parts.append(f".{item}")

    return "".join(parts)


def validate_fixture(
    fixture_path: Path,
    *,
    should_pass: bool,
    definitions: list[SchemaDefinition],
    registry: Registry,
) -> list[str]:
    definition = find_fixture_schema(fixture_path, definitions)
    instance = load_json(fixture_path)

    validator = Draft202012Validator(
        definition.contents,
        registry=registry,
        format_checker=FormatChecker(),
    )

    try:
        errors = sorted(
            validator.iter_errors(instance),
            key=lambda error: (
                tuple(str(item) for item in error.absolute_path),
                error.message,
            ),
        )
    except NoSuchResource as exc:
        return [
            f"{fixture_path}: unresolved $ref while validating against "
            f"{definition.key}: {exc}"
        ]
    except Exception as exc:
        return [
            f"{fixture_path}: validation failed unexpectedly against "
            f"{definition.key}: {exc}"
        ]

    if should_pass:
        return [
            f"{fixture_path}: expected valid fixture for {definition.key}, "
            f"but {format_instance_path(error)} failed: {error.message}"
            for error in errors
        ]

    if not errors:
        return [
            f"{fixture_path}: expected invalid fixture for "
            f"{definition.key}, but validation passed"
        ]

    return []


def iter_refs(value: Any) -> list[str]:
    refs: list[str] = []

    if isinstance(value, dict):
        ref = value.get("$ref")
        if isinstance(ref, str):
            refs.append(ref)

        for child in value.values():
            refs.extend(iter_refs(child))

    elif isinstance(value, list):
        for child in value:
            refs.extend(iter_refs(child))

    return refs


def validate_references(
    definitions: list[SchemaDefinition],
    registry: Registry,
) -> None:
    for definition in definitions:
        base_uri = definition.contents["$id"]

        for reference in iter_refs(definition.contents):
            absolute_uri = urljoin(base_uri, reference)

            try:
                registry.get_or_retrieve(absolute_uri)
            except Exception as exc:
                raise ValidationFailureError(
                    message=(
                        f"{definition.path}: unresolved $ref "
                        f"{reference!r} -> {absolute_uri!r}"
                    )
                ) from exc


def collect_fixtures(
    schema_root: Path,
    *,
    major: int,
    fixture_kind: str,
) -> list[Path]:
    directory = schema_root / "fixtures" / fixture_kind / f"v{major}"

    if not directory.exists():
        raise ValidationFailureError(
            message=f"fixture directory does not exist: {directory}"
        )

    if not directory.is_dir():
        raise ValidationFailureError(
            message=f"fixture path is not a directory: {directory}"
        )

    return sorted(path for path in directory.rglob("*.json") if path.is_file())


def validate_repository(schema_root: Path) -> list[str]:
    manifest = load_manifest(schema_root)
    definitions = load_schemas(schema_root, manifest)
    registry = build_registry(definitions)
    entry_definitions = entrypoint_definitions(definitions, manifest)

    major = manifest["compatibility_major"]

    valid_fixtures = collect_fixtures(
        schema_root,
        major=major,
        fixture_kind="valid",
    )
    invalid_fixtures = collect_fixtures(
        schema_root,
        major=major,
        fixture_kind="invalid",
    )

    validate_references(definitions, registry)

    failures: list[str] = []

    for fixture_path in valid_fixtures:
        failures.extend(
            validate_fixture(
                fixture_path,
                should_pass=True,
                definitions=definitions,
                registry=registry,
            )
        )

    for fixture_path in invalid_fixtures:
        failures.extend(
            validate_fixture(
                fixture_path,
                should_pass=False,
                definitions=definitions,
                registry=registry,
            )
        )

    fixture_counts = {
        definition.key: {"valid": 0, "invalid": 0} for definition in definitions
    }

    for fixture_path in valid_fixtures:
        definition = find_fixture_schema(fixture_path, definitions)
        fixture_counts[definition.key]["valid"] += 1

    for fixture_path in invalid_fixtures:
        definition = find_fixture_schema(fixture_path, definitions)
        fixture_counts[definition.key]["invalid"] += 1

    for definition in entry_definitions:
        counts = fixture_counts[definition.key]
        if counts["valid"] == 0:
            failures.append(f"{definition.key}: no valid fixtures found for v{major}")
        if counts["invalid"] == 0:
            failures.append(f"{definition.key}: no invalid fixtures found for v{major}")

    if not failures:
        print(
            "Schema validation passed: "
            f"{len(definitions)} schemas, "
            f"{len(entry_definitions)} entrypoints, "
            f"{len(valid_fixtures)} valid fixtures, "
            f"{len(invalid_fixtures)} invalid fixtures, "
            f"schema set {manifest['schema_set_version']}"
        )

    return failures


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate the Kiln JSON Schema set and fixtures."
    )
    parser.add_argument(
        "--schema-root",
        type=Path,
        default=Path(__file__).resolve().parents[2] / "schemas",
        help=(
            "Schema directory containing manifest.json. "
            "Defaults to the schemas directory."
        ),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    schema_root = args.schema_root.resolve()

    try:
        failures = validate_repository(schema_root)
    except ValidationFailureError as exc:
        print(f"schema validation failed: {exc}", file=sys.stderr)
        return 1

    if failures:
        print(
            f"schema validation failed with {len(failures)} error(s):",
            file=sys.stderr,
        )

        for failure in failures:
            print(f"- {failure}", file=sys.stderr)

        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
