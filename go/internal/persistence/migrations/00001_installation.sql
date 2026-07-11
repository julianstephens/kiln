-- +goose Up
CREATE TABLE installation_metadata (
    singleton_key integer PRIMARY KEY CHECK (singleton_key = 1),
    installation_id text Not NULL UNIQUE,
    database_format_version int NOT NULL CHECK (database_format_version >= 1),
    schema_compatibility_major integer NOT NULL CHECK (schema_compatibility_major >= 1),
    minimum_runtime_version text,
    last_opened_runtime_version text,
    maintenance_state text NOT NULL DEFAULT 'normal' CHECK (maintenance_state IN ('normal', 'migration_required', 'migration_failed', 'maintenance', 'read_only')),
    maintenance_details_json text,
    created_at integer NOT NULL DEFAULT (unixepoch()),
    updated_at integer NOT NULL DEFAULT (unixepoch())
);

-- +goose Down
DROP TABLE installation_metadata;
