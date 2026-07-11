-- +goose up
CREATE TABLE workspaces (
  workspace_id text PRIMARY KEY,
  installation_id text NOT NULL REFERENCES installation_metadata(installation_id) ON DELETE CASCADE,
  display_name text NOT NULL,
  root_location text NOT NULL,
  filesystem_identity text,
  configuration_hash text,
  registered_at integer NOT NULL DEFAULT (unixepoch()),
  last_seen_at integer NOT NULL DEFAULT (unixepoch()),
  archived_at integer
);
CREATE INDEX idx_workspaces_installation_id_root_location on workspaces(installation_id, root_location);
CREATE INDEX idx_workspaces_installation_id_archived_at on workspaces(installation_id, archived_at);

-- +goose down
DROP TABLE workspaces;
DROP INDEX idx_workspaces_installation_id_root_location;
DROP INDEX idx_workspaces_installation_id_archived_at;
