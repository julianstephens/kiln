import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

DEFAULT_SCHEMA_ROOT = Path(__file__).resolve().parents[2] / "schemas"
DEFAULT_OUTPUT_ROOT = Path(__file__).resolve().parents[2] / "python" / "kiln" / "schemas"
SCHEMA_ID_BASE = "https://kiln.cyborgdev.cloud/schemas"
BUNDLE_ID_FORMAT = f"{SCHEMA_ID_BASE}/python-models-{{domain}}.schema.json"
SHARED_SCHEMA_DOMAINS = ("common",)

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

    schema_set_version = manifest.get("schema_set_version")
    if not isinstance(schema_set_version, str) or not schema_set_version:
        raise GenerateModelsError(
            f"{manifest_path}: schema_set_version must be a non-empty string"
        )

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


def selected_schema_keys(manifest: dict[str, Any], *, only_entrypoints: bool) -> list[str]:
    field = "entrypoints" if only_entrypoints else "schemas"
    values = manifest.get(field)
    if not isinstance(values, list) or not values:
        raise GenerateModelsError(f"manifest field {field!r} must be a non-empty array")
    return list(values)


def schema_ref_for_key(schema_key: str, *, major: int) -> str:
    domain, contract = parse_schema_key(schema_key)
    return f"{domain}/v{major}/{contract}.schema.json"


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


def ensure_schema_files_exist(schema_root: Path, schema_keys: list[str], *, major: int) -> None:
    for schema_key in schema_keys:
        schema_path = schema_path_for_key(schema_root, schema_key, major=major)
        if not schema_path.exists():
            raise GenerateModelsError(
                f"schema listed in manifest does not exist: {schema_path}"
            )


def group_schema_keys_by_domain(schema_keys: list[str]) -> dict[str, list[str]]:
    groups: dict[str, list[str]] = {}
    for schema_key in schema_keys:
        domain, _contract = parse_schema_key(schema_key)
        groups.setdefault(domain, []).append(schema_key)
    return groups


def ordered_domains(schema_groups: dict[str, list[str]]) -> list[str]:
    domains = list(schema_groups)
    shared_domains = [domain for domain in SHARED_SCHEMA_DOMAINS if domain in schema_groups]
    non_shared_domains = [domain for domain in domains if domain not in SHARED_SCHEMA_DOMAINS]
    return [*shared_domains, *non_shared_domains]


def write_bundle_schema(path: Path, schema_keys: list[str], *, domain: str, major: int) -> None:
    defs = {
        def_name_for_key(schema_key): {"$ref": schema_ref_for_key(schema_key, major=major)}
        for schema_key in schema_keys
    }
    domain_name = python_name(domain)
    bundle = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": BUNDLE_ID_FORMAT.format(domain=domain_name),
        "title": f"Kiln {domain_name} generated Python models bundle",
        "type": "object",
        "$defs": defs,
        "properties": {
            python_name(schema_key): {"$ref": f"#/$defs/{def_name_for_key(schema_key)}"}
            for schema_key in schema_keys
        },
        "additionalProperties": False,
    }
    path.write_text(json.dumps(bundle, indent=4) + "\n", encoding="utf-8")


def write_package_init(
    output_root: Path,
    domains: list[str],
    *,
    compatibility_major: int,
    schema_set_version: str,
) -> None:
    init_path = output_root / "__init__.py"
    init_path.parent.mkdir(parents=True, exist_ok=True)
    domain_modules = [python_name(domain) for domain in domains]
    all_entries = "".join(f'    "{module}",\n' for module in domain_modules)
    content = (
        HEADER
        + "\nfrom __future__ import annotations\n\n"
        + "from importlib import import_module\n"
        + "from types import ModuleType\n\n"
        + f"COMPATIBILITY_MAJOR = {compatibility_major}\n"
        + f"SCHEMA_SET_VERSION = {schema_set_version!r}\n\n"
        + "__all__ = [\n"
        + '    "COMPATIBILITY_MAJOR",\n'
        + '    "SCHEMA_SET_VERSION",\n'
        + all_entries
        + "]\n\n"
        + "def __getattr__(name: str) -> ModuleType:\n"
        + "    if name not in __all__:\n"
        + "        raise AttributeError(f\"module {__name__!r} has no attribute {name!r}\")\n"
        + "    module = import_module(f\"{__name__}.{name}\")\n"
        + "    globals()[name] = module\n"
        + "    return module\n"
    )
    init_path.write_text(content, encoding="utf-8")


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
        help="Extra argument passed through to datamodel-codegen. May be repeated.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    schema_root = args.schema_root.resolve()
    output_root = args.output_root.resolve()

    try:
        manifest = load_manifest(schema_root)
        major = manifest["compatibility_major"]
        schema_set_version = manifest["schema_set_version"]
        schema_keys = selected_schema_keys(
            manifest,
            only_entrypoints=args.only_entrypoints,
        )
        ensure_schema_files_exist(schema_root, schema_keys, major=major)

        if not args.no_clean:
            clean_output_root(output_root, dry_run=args.dry_run)

        schema_groups = group_schema_keys_by_domain(schema_keys)
        domains = ordered_domains(schema_groups)
        bundle_paths: list[Path] = []

        try:
            for domain in domains:
                domain_schema_keys = schema_groups[domain]
                domain_name = python_name(domain)
                bundle_path = schema_root / f".python-models-{domain_name}.schema.json"
                domain_output_root = output_root / domain_name
                bundle_paths.append(bundle_path)

                if args.dry_run:
                    print(f"would write temporary bundle schema: {bundle_path}")
                else:
                    write_bundle_schema(
                        bundle_path,
                        domain_schema_keys,
                        domain=domain,
                        major=major,
                    )

                run_datamodel_codegen(
                    bundle_path=bundle_path,
                    schema_root=schema_root,
                    output_root=domain_output_root,
                    extra_args=args.extra_arg,
                    dry_run=args.dry_run,
                )
        finally:
            if not args.dry_run:
                for bundle_path in bundle_paths:
                    bundle_path.unlink(missing_ok=True)

        if not args.dry_run:
            write_package_init(
                output_root,
                domains,
                compatibility_major=major,
                schema_set_version=schema_set_version,
            )

    except GenerateModelsError as exc:
        print(f"model generation failed: {exc}", file=sys.stderr)
        return 1

    print(f"Generated schema models for {len(schema_keys)} schema(s) in {output_root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
