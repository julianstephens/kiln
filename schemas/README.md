# Kiln schemas

This directory contains the language-neutral contracts used across Kiln process boundaries.

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

## Fixtures

`fixtures/valid/` contains documents that must pass validation.

`fixtures/invalid/` contains documents that must fail validation.

Run:

```bash
make  validate-schemas
```
