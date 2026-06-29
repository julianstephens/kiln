# Kiln cross-language contract fixtures

These fixtures are shared by Python and Go tests to prove generated schema models can deserialize, validate, and serialize the same schema-defined messages.

The fixtures intentionally exercise stable first-slice schema shapes where both languages enforce the same core constraints. Full JSON Schema conformance remains covered by the schema validation fixtures under `schemas/**/fixtures`.
