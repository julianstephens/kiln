package persistence

import (
	"database/sql"
	"errors"
	"testing"

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

func TestInitializeDatabase(t *testing.T) {
	t.Parallel()

	t.Run("inserts installation row", func(t *testing.T) {
		t.Parallel()

		db := openInMemoryDB(t)
		createInstallationTable(t, db, "installation_metadata")

		if err := initializeDatabase(db); err != nil {
			t.Fatalf("initializeDatabase returned error: %v", err)
		}

		var count int
		if err := db.QueryRow(`SELECT COUNT(*) FROM installation_metadata;`).Scan(&count); err != nil {
			t.Fatalf("failed to count installation rows: %v", err)
		}
		if count != 1 {
			t.Fatalf("installation row count = %d, want 1", count)
		}
	})

	t.Run("returns error when table is missing", func(t *testing.T) {
		t.Parallel()

		db := openInMemoryDB(t)
		err := initializeDatabase(db)
		if err == nil {
			t.Fatal("initializeDatabase error = nil, want error")
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
