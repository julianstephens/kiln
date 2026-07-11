package persistence

import (
	"database/sql"
	"errors"
	"testing"

	"github.com/julianstephens/kiln/go/internal/util"
	"github.com/julianstephens/kiln/go/schema"
	_ "github.com/mattn/go-sqlite3"
)

func TestValidateStorePath(t *testing.T) {
	t.Parallel()

	tests := []struct {
		name      string
		input     string
		wantPath  string
		wantError bool
	}{
		{
			name:      "empty path",
			input:     "",
			wantError: true,
		},
		{
			name:      "relative path",
			input:     "relative/store.db",
			wantError: true,
		},
		{
			name:      "non db extension",
			input:     "/tmp/store.sqlite",
			wantError: true,
		},
		{
			name:     "in memory",
			input:    ":memory:",
			wantPath: ":memory:",
		},
		{
			name:     "absolute db path",
			input:    "/tmp/../tmp/kiln.db",
			wantPath: "/tmp/kiln.db",
		},
	}

	for _, tt := range tests {
		tt := tt
		t.Run(tt.name, func(t *testing.T) {
			t.Parallel()

			got, err := validateStorePath(tt.input)
			if tt.wantError {
				if err == nil {
					t.Fatalf("validateStorePath(%q) error = nil, want error", tt.input)
				}
				var storeErr *Error
				if !errors.As(err, &storeErr) {
					t.Fatalf("validateStorePath(%q) error type = %T, want *Error", tt.input, err)
				}
				if storeErr.Code != CodeInvalidPath {
					t.Fatalf("validateStorePath(%q) error code = %q, want %q", tt.input, storeErr.Code, CodeInvalidPath)
				}
				return
			}

			if err != nil {
				t.Fatalf("validateStorePath(%q) unexpected error: %v", tt.input, err)
			}
			if got == nil {
				t.Fatalf("validateStorePath(%q) returned nil path", tt.input)
			}
			if *got != tt.wantPath {
				t.Fatalf("validateStorePath(%q) = %q, want %q", tt.input, *got, tt.wantPath)
			}
		})
	}
}

func TestUpdateInstallationMetadata(t *testing.T) {
	t.Parallel()

	t.Run("inserts installation row when database is new", func(t *testing.T) {
		t.Parallel()

		db := openInMemoryDB(t)
		createInstallationTable(t, db, "installation_metadata")

		if err := updateInstallationMetadata(db, "normal", false); err != nil {
			t.Fatalf("updateInstallationMetadata returned error: %v", err)
		}

		var count int
		var maintenanceState string
		var compatibilityMajor int
		var lastOpenedVersion string
		if err := db.QueryRow(`
			SELECT COUNT(*), maintenance_state, schema_compatibility_major, last_opened_runtime_version
			FROM installation_metadata;
		`).Scan(&count, &maintenanceState, &compatibilityMajor, &lastOpenedVersion); err != nil {
			t.Fatalf("failed to read installation row: %v", err)
		}
		if count != 1 {
			t.Fatalf("installation row count = %d, want 1", count)
		}
		if maintenanceState != "normal" {
			t.Fatalf("maintenance_state = %q, want %q", maintenanceState, "normal")
		}
		if compatibilityMajor != schema.CompatibilityMajor {
			t.Fatalf("schema_compatibility_major = %d, want %d", compatibilityMajor, schema.CompatibilityMajor)
		}
		if lastOpenedVersion != util.RuntimeProtocolVersion {
			t.Fatalf("last_opened_runtime_version = %q, want %q", lastOpenedVersion, util.RuntimeProtocolVersion)
		}
	})

	t.Run("updates existing installation row", func(t *testing.T) {
		t.Parallel()

		db := openInMemoryDB(t)
		createInstallationTable(t, db, "installation_metadata")

		_, err := db.Exec(`
			INSERT INTO installation_metadata (
				installation_id,
				database_format_version,
				schema_compatibility_major,
				minimum_runtime_version,
				last_opened_runtime_version,
				maintenance_state
			) VALUES (?, ?, ?, ?, ?, ?);
		`, "existing-installation", 0, 0, "old-min", "old-open", "normal")
		if err != nil {
			t.Fatalf("failed to seed installation row: %v", err)
		}

		if err := updateInstallationMetadata(db, "migration_failed", true); err != nil {
			t.Fatalf("updateInstallationMetadata returned error: %v", err)
		}

		var installationID string
		var maintenanceState string
		var dbFormatVersion int
		var compatibilityMajor int
		if err := db.QueryRow(`
			SELECT installation_id, maintenance_state, database_format_version, schema_compatibility_major
			FROM installation_metadata LIMIT 1;
		`).Scan(&installationID, &maintenanceState, &dbFormatVersion, &compatibilityMajor); err != nil {
			t.Fatalf("failed to read updated installation row: %v", err)
		}
		if installationID != "existing-installation" {
			t.Fatalf("installation_id = %q, want %q", installationID, "existing-installation")
		}
		if maintenanceState != "migration_failed" {
			t.Fatalf("maintenance_state = %q, want %q", maintenanceState, "migration_failed")
		}
		if dbFormatVersion != DBFormatVersion {
			t.Fatalf("database_format_version = %d, want %d", dbFormatVersion, DBFormatVersion)
		}
		if compatibilityMajor != schema.CompatibilityMajor {
			t.Fatalf("schema_compatibility_major = %d, want %d", compatibilityMajor, schema.CompatibilityMajor)
		}
	})

	t.Run("returns error when table is missing", func(t *testing.T) {
		t.Parallel()

		db := openInMemoryDB(t)
		err := updateInstallationMetadata(db, "normal", false)
		if err == nil {
			t.Fatal("updateInstallationMetadata error = nil, want error")
		}
	})
}

func openInMemoryDB(t *testing.T) *sql.DB {
	t.Helper()

	db, err := sql.Open("sqlite3", ":memory:")
	if err != nil {
		t.Fatalf("failed to open in-memory sqlite database: %v", err)
	}
	t.Cleanup(func() {
		_ = db.Close()
	})

	return db
}

func createInstallationTable(t *testing.T, db *sql.DB, tableName string) {
	t.Helper()

	// #nosec G202 -- tableName is derived from a controlled test input and does not pose a SQL injection risk
	createTableSQL := `
		CREATE TABLE ` + tableName + ` (
			installation_id TEXT NOT NULL,
			database_format_version INTEGER NOT NULL,
			schema_compatibility_major INTEGER NOT NULL,
			minimum_runtime_version TEXT,
			last_opened_runtime_version TEXT,
			maintenance_state TEXT NOT NULL
		);
	`

	if _, err := db.Exec(createTableSQL); err != nil {
		t.Fatalf("failed to create installation table: %v", err)
	}
}
