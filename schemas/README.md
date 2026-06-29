# Kiln schemas

This directory contains the language-neutral contracts used across Kiln process boundaries. Transport request and response payloads are programmatically wrapped in JSON-RPC envelopes, but the payloads themselves are defined by these schemas.

## Schema versioning

Each schema must define:

- JSON Schema draft 2020-12;
- a stable `$id`;
- an explicit contract version;
- required and optional properties;
- whether unknown properties are accepted.

Schema IDs use this form:

```text
https://kiln.cyborgdev.cloud/schemas/<domain>/v<major>/<contract>.schema.json
```

Compatible additive changes may retain the same major version.

Breaking changes require a new major version.

## Manifest semantics

`schemas/manifest.json` contains two lists:

- `schemas`: every maintained schema, including reusable component schemas referenced by other contracts
- `entrypoints`: top-level documents that callers may validate independently

A component schema belongs in `schemas` even when it is used only through $ref. It belongs in `entrypoints` only when it is also a supported standalone contract.

## Validate schemas

```sh
make validate-schemas
```

Or invoke the tool directly:

```sh
uv run validateschemas
```

Validation checks:

- manifest structure
- registered schema paths
- schema IDs and release metadata
- reference resolution
- valid fixtures
- invalid fixtures

## Create a schema

Use `newschema` to create a schema skeleton and register it in the manifest:

```sh
uv run newschema repository example-contract
```

Create a top-level entrypoint with fixture placeholders:

```sh
uv run newschema repository example-contract \
  --entrypoint \
  --valid-case basic \
  --invalid-case missing-required-field
```

The command creates the files and manifest entries. Generated fixture bodies are placeholders and must be edited to express meaningful valid and invalid cases.

After editing:

```sh
make validate-schemas
```
