-- +goose up
CREATE TABLE artifacts (
  artifact_id text PRIMARY KEY,
  installation_id text NOT NULL REFERENCES installation_metadata(installation_id) ON DELETE CASCADE,
  blob_id text NOT NULL REFERENCES artifact_blobs(blob_id) ON DELETE CASCADE,
  repository_id text REFERENCES repositories(repository_id) ON DELETE SET NULL,
  validation_id text,
  artifact_kind text NOT NULL,
  content_type text NOT NULL,
  canonical_content_hash text NOT NULL,
  uncompressed_size integer NOT NULL,
  stored_size integer NOT NULL,
  compression text NOT NULL,
  retention_class text NOT NULL,
  deletion_state text NOT NULL CHECK (deletion_state IN ('retained', 'tombstoned', 'deleted')),
  tombstoned_at integer,
  deleted_at integer,
  created_at integer NOT NULL DEFAULT (unixepoch())
);
CREATE INDEX idx_artifacts_installation_id_canonical_content_hash on artifacts(installation_id, canonical_content_hash);
CREATE INDEX idx_artifacts_repository_id_artifact_kind on artifacts(repository_id, artifact_kind);
CREATE INDEX idx_artifacts_deletion_state_created_at on artifacts(deletion_state, created_at);


-- +goose down
DROP TABLE artifacts;
DROP INDEX idx_artifacts_installation_id_canonical_content_hash;
DROP INDEX idx_artifacts_repository_id_artifact_kind;
DROP INDEX idx_artifacts_deletion_state_created_at;

