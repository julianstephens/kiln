-- +goose up
CREATE TABLE repositories (
  repository_id text PRIMARY KEY,
  workspace_id text NOT NULL REFERENCES workspaces(workspace_id) ON DELETE CASCADE,
  display_name text NOT NULL,
  source_kind text NOT NULL,
  canonical_source_identity text,
  current_repository_version_id text REFERENCES repository_versions(repository_version_id) ON DELETE SET NULL,
  current_workspace_version_id text REFERENCES workspace_versions(workspace_version_id) ON DELETE SET NULL,
  current_index_generation_id text REFERENCES index_generations(index_generation_id) ON DELETE SET NULL,
  registered_at integer NOT NULL DEFAULT (unixepoch()),
  last_accessed_at integer NOT NULL DEFAULT (unixepoch()),
  archived_at integer
);
CREATE INDEX idx_repositories_workspace_id_canonical_source_identity on repositories(workspace_id, canonical_source_identity);
CREATE INDEX idx_repositories_workspace_id_archived_at on repositories(workspace_id, archived_at);

-- +goose down
DROP TABLE repositories;
DROP INDEX idx_repositories_workspace_id_canonical_source_identity;
DROP INDEX idx_repositories_workspace_id_archived_at;

