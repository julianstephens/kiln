-- +goose up
CREATE TABLE repository_versions (
  repository_version_id text PRIMARY KEY,
  repository_id text NOT NULL REFERENCES repositories(repository_id) ON DELETE CASCADE,
  parent_repository_version_id text REFERENCES repository_versions(repository_version_id) ON DELETE SET NULL,
  source_revision text,
  snapshot_artifact_id text REFERENCES artifacts(artifact_id) ON DELETE SET NULL,
  content_digest text NOT NULL,
  index_compatibility_version integer NOT NULL,
  creation_reason text NOT NULL,
  state text NOT NULL DEFAULT 'registered' CHECK (state IN ('registered', 'preparing', 'ready', 'superseded', 'invalid', 'failed')),
  created_at integer NOT NULL DEFAULT (unixepoch()),
  ready_at integer,
  superseded_at integer,
  failure_error_json text
);
CREATE INDEX idx_repository_versions_repository_id_content_digest on repository_versions(repository_id, content_digest);
CREATE INDEX idx_repository_versions_repository_id_state on repository_versions(repository_id, state);
CREATE INDEX idx_repository_versions_repository_id_created_at on repository_versions(repository_id, created_at);

-- +goose down
DROP TABLE repository_versions;
DROP INDEX idx_repository_versions_repository_id_content_digest;
DROP INDEX idx_repository_versions_repository_id_state;
DROP INDEX idx_repository_versions_repository_id_created_at;
