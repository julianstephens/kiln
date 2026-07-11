-- +goose up
CREATE TABLE runs (
  run_id text PRIMARY KEY,
  installation_id text NOT NULL REFERENCES installation_metadata(installation_id) ON DELETE CASCADE,
  idempotency_key text,
  task_hash text NOT NULL,
  repository_id text REFERENCES repositories(repository_id) ON DELETE CASCADE,
  requested_model text,
  requested_context_policy text,
  requested_security_profile text,
  validation_required integer NOT NULL DEFAULT 0,
  created_at integer NOT NULL DEFAULT (unixepoch())
); 
CREATE INDEX idx_runs_installation_id_idempotency_key on runs(installation_id, idempotency_key);
CREATE INDEX idx_runs_repository_id_created_at on runs(repository_id, created_at);
CREATE INDEX idx_runs_created_at on runs(created_at);

CREATE TABLE run_specifications (
  run_id integer NOT NULL REFERENCES runs(run_id) ON DELETE CASCADE,
  specification_hash text NOT NULL,
  specification_json text,
  specification_artifact_id text REFERENCES artifacts(artifact_id) ON DELETE CASCADE,
  CHECK ((specification_json IS NOT NULL AND specification_artifact_id IS NULL) OR (specification_json IS NULL AND specification_artifact_id IS NOT NULL))
);

-- +goose down
DROP TABLE runs;
DROP INDEX idx_runs_installation_id_idempotency_key;
DROP INDEX idx_runs_repository_id_created_at;
DROP INDEX idx_runs_created_at;
DROP TABLE run_specifications;
