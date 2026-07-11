-- +goose up
CREATE TABLE workspace_versions (
  workspace_version_id text PRIMARY KEY,
  workspace_id text NOT NULL REFERENCES workspaces(workspace_id) ON DELETE CASCADE,
  base_repository_version_id text REFERENCES repository_versions(repository_version_id) ON DELETE SET NULL,
  parent_workspace_version_id text REFERENCES workspace_versions(workspace_version_id) ON DELETE SET NULL,
  version_sequence integer NOT NULL CHECK (version_sequence >= 1),
  mutation_set_hash text,
  affected_paths_json text,
  state text NOT NULL DEFAULT 'created' CHECK (state IN ('created', 'index_stale', 'synchronizing', 'synchronized', 'superceded')),
  created_at integer NOT NULL DEFAULT (unixepoch()),
  synchronized_at integer,
  superseded_at integer
);
CREATE INDEX idx_workspace_versions_workspace_id_version_sequence on workspace_versions(workspace_id, version_sequence);
CREATE INDEX idx_workspace_versions_workspace_id_state on workspace_versions(workspace_id, state);

-- +goose down
DROP TABLE workspace_versions;
DROP INDEX idx_workspace_versions_workspace_id_version_sequence;
DROP INDEX idx_workspace_versions_workspace_id_state;