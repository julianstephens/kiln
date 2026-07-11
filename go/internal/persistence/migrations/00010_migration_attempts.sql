-- +goose up
CREATE TABLE migration_attempts (
  owner_runtime_session_id text REFERENCES runtime_sessions(runtime_session_id) ON DELETE CASCADE,
  started_at integer NOT NULL,
  completed_at integer,
  from_version integer NOT NULL,
  target_version integer NOT NULL,
  status text NOT NULL,
  failed_migration_version integer,
  error_json text
);
CREATE INDEX idx_migration_attempts_started_at ON migration_attempts(started_at);
CREATE INDEX idx_migration_attempts_status_started_at ON migration_attempts(status, started_at);

-- +goose down
DROP TABLE migration_attempts;
DROP INDEX idx_migration_attempts_started_at;
DROP INDEX idx_migration_attempts_status_started_at;
