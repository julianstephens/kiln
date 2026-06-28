import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


DEFAULT_SCHEMA_ROOT = Path(__file__).resolve().parents[2] / "schemas"
DEFAULT_OUTPUT_ROOT = (
    Path(__file__).resolve().parents[2] / "python" / "kiln" / "schemas"
)

BUNDLE_ID = (
    "https://kiln.cyborgdev.cloud/schemas/generated/python-models-bundle.schema.json"
)

HEADER = '''"""
Generated Pydantic v2 models for Kiln JSON Schemas.

Do not edit this package by hand. Regenerate with:

    uv run generatemodels
"""
'''


class GenerateModelsError(Exception):
    pass


def python_name(value: str) -> str:
    normalized = re.sub(r"[^0-9a-zA-Z_]", "_", value)
    normalized = re.sub(r"_+", "_", normalized).strip("_").lower()

    if not normalized:
        raise GenerateModelsError(f"could not convert {value!r} to a Python name")

    if normalized[0].isdigit():
        normalized = f"schema_{normalized}"

    return normalized


def def_name_for_key(schema_key: str) -> str:
    return python_name(schema_key).title().replace("_", "")


def parse_schema_key(schema_key: str) -> tuple[str, str]:
    parts = schema_key.split("/", maxsplit=1)

    if len(parts) != 2 or not parts[0] or not parts[1]:
        raise GenerateModelsError(
            f"invalid schema key {schema_key!r}; expected '<domain>/<contract>'"
        )

    return parts[0], parts[1]


def load_json(path: Path) -> Any:
    try:
        with path.open(encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError as exc:
        raise GenerateModelsError(f"file does not exist: {path}") from exc
    except json.JSONDecodeError as exc:
        raise GenerateModelsError(
            f"{path}:{exc.lineno}:{exc.colno}: invalid JSON: {exc.msg}"
        ) from exc
    except OSError as exc:
        raise GenerateModelsError(f"could not read {path}: {exc}") from exc


def load_manifest(schema_root: Path) -> dict[str, Any]:
    manifest_path = schema_root / "manifest.json"
    manifest = load_json(manifest_path)

    if not isinstance(manifest, dict):
        raise GenerateModelsError(f"{manifest_path}: expected JSON object")

    compatibility_major = manifest.get("compatibility_major")
    if (
        not isinstance(compatibility_major, int)
        or isinstance(compatibility_major, bool)
        or compatibility_major < 1
    ):
        raise GenerateModelsError(
            f"{manifest_path}: compatibility_major must be a positive integer"
        )

    schemas = manifest.get("schemas")
    if not isinstance(schemas, list) or not schemas:
        raise GenerateModelsError(f"{manifest_path}: schemas must be a non-empty array")

    for index, schema_key in enumerate(schemas):
        if not isinstance(schema_key, str) or not schema_key:
            raise GenerateModelsError(
                f"{manifest_path}: schemas[{index}] must be a non-empty string"
            )
        parse_schema_key(schema_key)

    entrypoints = manifest.get("entrypoints")
    if entrypoints is not None:
        if not isinstance(entrypoints, list) or not entrypoints:
            raise GenerateModelsError(
                f"{manifest_path}: entrypoints must be a non-empty array"
            )

        schema_key_set = set(schemas)

        for index, schema_key in enumerate(entrypoints):
            if not isinstance(schema_key, str) or not schema_key:
                raise GenerateModelsError(
                    f"{manifest_path}: entrypoints[{index}] must be a non-empty string"
                )
            parse_schema_key(schema_key)

            if schema_key not in schema_key_set:
                raise GenerateModelsError(
                    f"{manifest_path}: entrypoint {schema_key!r} is not declared in schemas"
                )

    return manifest


def selected_schema_keys(
    manifest: dict[str, Any], *, only_entrypoints: bool
) -> list[str]:
    field = "entrypoints" if only_entrypoints else "schemas"
    values = manifest.get(field)

    if not isinstance(values, list) or not values:
        raise GenerateModelsError(f"manifest field {field!r} must be a non-empty array")

    return list(values)


def schema_id_for_key(schema_key: str, *, major: int) -> str:
    domain, contract = parse_schema_key(schema_key)
    return (
        f"https://kiln.cyborgdev.cloud/schemas/{domain}/v{major}/{contract}.schema.json"
    )


def schema_path_for_key(schema_root: Path, schema_key: str, *, major: int) -> Path:
    domain, contract = parse_schema_key(schema_key)
    contract_parts = contract.split("/")

    return (
        schema_root
        / domain
        / f"v{major}"
        / Path(*contract_parts[:-1])
        / f"{contract_parts[-1]}.schema.json"
    )


def ensure_schema_files_exist(
    schema_root: Path,
    schema_keys: list[str],
    *,
    major: int,
) -> None:
    for schema_key in schema_keys:
        schema_path = schema_path_for_key(schema_root, schema_key, major=major)
        if not schema_path.exists():
            raise GenerateModelsError(
                f"schema listed in manifest does not exist: {schema_path}"
            )


def write_bundle_schema(
    path: Path,
    schema_keys: list[str],
    *,
    major: int,
) -> None:
    """
    Create one artificial schema that references every selected Kiln schema.

    This avoids per-schema output ambiguity in datamodel-code-generator:
    - some schemas want file output
    - some schemas with external refs want directory output

    Generating once into one package directory is more stable.
    """
    defs: dict[str, Any] = {}

    for schema_key in schema_keys:
        defs[def_name_for_key(schema_key)] = {
            "$ref": schema_id_for_key(schema_key, major=major)
        }

    bundle = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": BUNDLE_ID,
        "title": "Kiln generated Python models bundle",
        "type": "object",
        "$defs": defs,
        "properties": {
            python_name(schema_key): {"$ref": f"#/$defs/{def_name_for_key(schema_key)}"}
            for schema_key in schema_keys
        },
        "additionalProperties": False,
    }

    path.write_text(json.dumps(bundle, indent=4) + "\n", encoding="utf-8")


def write_init(output_root: Path) -> None:
    init_path = output_root / "__init__.py"
    init_path.parent.mkdir(parents=True, exist_ok=True)

    if init_path.exists():
        current = init_path.read_text(encoding="utf-8")
        if "Generated Pydantic v2 models for Kiln JSON Schemas" in current:
            return

    init_path.write_text(HEADER, encoding="utf-8")


def clean_output_root(output_root: Path, *, dry_run: bool) -> None:
    if not output_root.exists():
        return

    if dry_run:
        print(f"would remove {output_root}")
        return

    shutil.rmtree(output_root)


def run_datamodel_codegen(
    *,
    bundle_path: Path,
    schema_root: Path,
    output_root: Path,
    extra_args: list[str],
    dry_run: bool,
) -> None:
    command = [
        "datamodel-codegen",
        "--input",
        str(bundle_path),
        "--input-file-type",
        "jsonschema",
        "--output-model-type",
        "pydantic_v2.BaseModel",
        "--output",
        str(output_root),
        "--target-python-version",
        "3.13",
        "--use-annotated",
        "--field-constraints",
        "--use-standard-collections",
        "--use-union-operator",
        "--formatters",
        "ruff-check",
        "ruff-format",
        "--allow-remote-refs",
        "--custom-file-header",
        HEADER,
        *extra_args,
    ]

    print(f"generate schema models -> {output_root}")

    if dry_run:
        print("  " + " ".join(command))
        return

    output_root.mkdir(parents=True, exist_ok=True)

    try:
        subprocess.run(command, check=True, cwd=schema_root.parents[0])
    except FileNotFoundError as exc:
        raise GenerateModelsError(
            "datamodel-codegen not found. Install dev dependencies with `uv sync --dev`."
        ) from exc
    except subprocess.CalledProcessError as exc:
        raise GenerateModelsError(
            f"datamodel-codegen failed with exit code {exc.returncode}"
        ) from exc


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate Pydantic v2 models from Kiln JSON Schemas."
    )
    parser.add_argument(
        "--schema-root",
        type=Path,
        default=DEFAULT_SCHEMA_ROOT,
        help="Schema directory containing manifest.json.",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=DEFAULT_OUTPUT_ROOT,
        help="Output package root for generated Python models.",
    )
    parser.add_argument(
        "--only-entrypoints",
        action="store_true",
        help="Generate only manifest entrypoints instead of every declared schema.",
    )
    parser.add_argument(
        "--no-clean",
        action="store_true",
        help="Do not delete the output root before generation.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print generation command without writing files.",
    )
    parser.add_argument(
        "--extra-arg",
        action="append",
        default=[],
        help=("Extra argument passed through to datamodel-codegen. May be repeated."),
    )

    return parser.parse_args()


def main() -> int:
    args = parse_args()

    schema_root = args.schema_root.resolve()
    output_root = args.output_root.resolve()

    try:
        manifest = load_manifest(schema_root)
        major = manifest["compatibility_major"]

        schema_keys = selected_schema_keys(
            manifest,
            only_entrypoints=args.only_entrypoints,
        )

        ensure_schema_files_exist(schema_root, schema_keys, major=major)

        if not args.no_clean:
            clean_output_root(output_root, dry_run=args.dry_run)

        if args.dry_run:
            bundle_path = output_root / "_kiln_models_bundle.schema.json"
            print(f"would write temporary bundle schema: {bundle_path}")
            run_datamodel_codegen(
                bundle_path=bundle_path,
                schema_root=schema_root,
                output_root=output_root,
                extra_args=args.extra_arg,
                dry_run=True,
            )
            return 0

        with tempfile.TemporaryDirectory(prefix="kiln-schema-models-") as temp_dir:
            bundle_path = Path(temp_dir) / "kiln-models-bundle.schema.json"
            write_bundle_schema(bundle_path, schema_keys, major=major)

            run_datamodel_codegen(
                bundle_path=bundle_path,
                schema_root=schema_root,
                output_root=output_root,
                extra_args=args.extra_arg,
                dry_run=False,
            )

        write_init(output_root)

    except GenerateModelsError as exc:
        print(f"model generation failed: {exc}", file=sys.stderr)
        return 1

    print(f"Generated schema models for {len(schema_keys)} schema(s) in {output_root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
