-- +goose up
CREATE TABLE runtime_sessions (
  runtime_session_id text PRIMARY KEY,
  installation_id text NOT NULL REFERENCES installation_metadata(installation_id) ON DELETE CASCADE,
  runtime_protocol_version text,
  schema_set_version text,
  compatibility_major int,
  runtime_name text NOT NULL,
  runtime_version text NOT NULL,
  runtime_build_commit text,
  runtime_build_date text,
  client_name text,
  client_version text,
  state text NOT NULL CHECK (state IN ('starting', 'initializing', 'ready', 'draining', 'exited', 'failed')),
  process_id integer,
  started_at integer NOT NULL DEFAULT (unixepoch()),
  initialization_started_at integer,
  ready_at integer,
  draining_at integer,
  exited_at integer,
  final_exit_class text CHECK (final_exit_class IN ('graceful_exit', 'protocol_eof', 'startup_failure', 'initialize_failure', 'unexpected_exit', 'timeout', 'forced_kill', 'crash')),
  raw_exit_code integer,
  normalized_exit_code integer,
  normalized_signal text,
  expected_exit integer,
  last_fatal_error_json text,
  stder_tail_artifact_id text REFERENCES artifacts(artifact_id) ON DELETE SET NULL,
  state_version integer NOT NULL DEFAULT 1,
  last_heartbeat_at integer
);
CREATE INDEX idx_runtime_sessions_installation_id_started_at on runtime_sessions(installation_id, started_at);
CREATE INDEX idx_runtime_sessions_state_last_heartbeat_at on runtime_sessions(state, last_heartbeat_at);

-- +goose down
DROP TABLE runtime_sessions;
DROP INDEX idx_runtime_sessions_installation_id_started_at;
DROP INDEX idx_runtime_sessions_state_last_heartbeat_at;
