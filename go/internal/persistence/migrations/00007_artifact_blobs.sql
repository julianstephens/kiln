-- +goose up
CREATE TABLE artifact_blobs (
  blob_id text PRIMARY KEY,
  canonical_content_hash text NOT NULL,
  compression text NOT NULL,
  uncompressed_size integer NOT NULL CHECK (uncompressed_size >= 0),
  stored_size integer NOT NULL CHECK (stored_size >= 0),
  stored_bytes blob,
  created_at integer NOT NULL DEFAULT (unixepoch())
);
CREATE INDEX idx_artifact_blobs_canonical_content_hash_compression on artifact_blobs(canonical_content_hash, compression);


-- +goose down
DROP TABLE artifact_blobs;
DROP INDEX idx_artifact_blobs_canonical_content_hash_compression;