package persistence_test

import (
	"context"
	"database/sql"
	"errors"
	"path/filepath"
	"strings"
	"testing"

	"github.com/julianstephens/kiln/go/internal/persistence"
	"github.com/julianstephens/kiln/go/internal/util"
	runtime_error "github.com/julianstephens/kiln/go/schema/runtime/error"
	_ "github.com/mattn/go-sqlite3"
)

func installationID(t *testing.T, db *sql.DB) string {
	installationID := ""
	if err := db.QueryRow(`SELECT installation_id FROM installation_metadata WHERE singleton_key = 1`).
		Scan(&installationID); err != nil {
		t.Fatalf("failed to retrieve installation ID: %v", err)
	}
	return installationID
}

type installationMetadataSnapshot struct {
	DatabaseFormatVersion    int64
	SchemaCompatibilityMajor int
	LastOpenedRuntimeVersion string
	UpdatedAt                int64
}

func loadInstallationMetadata(t *testing.T, db *sql.DB) installationMetadataSnapshot {
	t.Helper()

	var snapshot installationMetadataSnapshot
	if err := db.QueryRow(`
		SELECT database_format_version, schema_compatibility_major, last_opened_runtime_version, updated_at
		FROM installation_metadata
		WHERE singleton_key = 1
	`).Scan(
		&snapshot.DatabaseFormatVersion,
		&snapshot.SchemaCompatibilityMajor,
		&snapshot.LastOpenedRuntimeVersion,
		&snapshot.UpdatedAt,
	); err != nil {
		t.Fatalf("failed to load installation metadata: %v", err)
	}

	return snapshot
}

func TestOpenCreatesInstallationMetadata(t *testing.T) {
	path := filepath.Join(t.TempDir(), "kiln.db")
	cfg := testConfig(path)

	store, err := persistence.Open(context.Background(), cfg)
	if err != nil {
		t.Fatalf("Open() error = %v", err)
	}
	defer func() {
		_ = store.Close()
	}()

	var installationID string
	err = store.GetDB().QueryRow(`
        SELECT installation_id
        FROM installation_metadata
        WHERE singleton_key = 1
    `).Scan(&installationID)
	if err != nil {
		t.Fatalf("load installation identity: %v", err)
	}

	if installationID == "" {
		t.Fatal("installation identity is empty")
	}
}

func TestOpenPreservesInstallationIdentity(t *testing.T) {
	ctx := context.Background()
	path := filepath.Join(t.TempDir(), "kiln.db")
	cfg := testConfig(path)

	first, err := persistence.Open(ctx, cfg)
	if err != nil {
		t.Fatalf("first Open(): %v", err)
	}
	firstID := installationID(t, first.GetDB())

	if err := first.Close(); err != nil {
		t.Fatalf("first Close(): %v", err)
	}

	second, err := persistence.Open(ctx, cfg)
	if err != nil {
		t.Fatalf("second Open(): %v", err)
	}
	defer func() {
		_ = second.Close()
	}()

	secondID := installationID(t, second.GetDB())

	if firstID != secondID {
		t.Fatalf(
			"installation identity changed: first=%q second=%q",
			firstID,
			secondID,
		)
	}
}

func TestOpenRefreshesOpenTimeMetadataOnReopen(t *testing.T) {
	ctx := context.Background()
	path := filepath.Join(t.TempDir(), "kiln.db")
	cfg := testConfig(path)

	first, err := persistence.Open(ctx, cfg)
	if err != nil {
		t.Fatalf("first Open(): %v", err)
	}
	if _, err := first.GetDB().Exec(`
		UPDATE installation_metadata
		SET last_opened_runtime_version = ?, updated_at = 1
		WHERE singleton_key = 1
	`, "old-runtime"); err != nil {
		t.Fatalf("seed stale reopen metadata: %v", err)
	}
	if err := first.Close(); err != nil {
		t.Fatalf("first Close(): %v", err)
	}

	second, err := persistence.Open(ctx, cfg)
	if err != nil {
		t.Fatalf("second Open(): %v", err)
	}
	defer func() {
		_ = second.Close()
	}()

	snapshot := loadInstallationMetadata(t, second.GetDB())
	if snapshot.LastOpenedRuntimeVersion != util.RuntimeProtocolVersion {
		t.Fatalf(
			"last_opened_runtime_version = %q, want %q",
			snapshot.LastOpenedRuntimeVersion,
			util.RuntimeProtocolVersion,
		)
	}
	if snapshot.UpdatedAt <= 1 {
		t.Fatalf("updated_at = %d, want value > 1", snapshot.UpdatedAt)
	}
}

func TestOpenFailsOnUnsupportedStoredDatabaseFormat(t *testing.T) {
	ctx := context.Background()
	path := filepath.Join(t.TempDir(), "kiln.db")
	cfg := testConfig(path)

	store, err := persistence.Open(ctx, cfg)
	if err != nil {
		t.Fatalf("first Open(): %v", err)
	}
	if _, err := store.GetDB().Exec(`
		UPDATE installation_metadata
		SET database_format_version = 9999
		WHERE singleton_key = 1
	`); err != nil {
		t.Fatalf("seed unsupported database format version: %v", err)
	}
	if err := store.Close(); err != nil {
		t.Fatalf("first Close(): %v", err)
	}

	_, err = persistence.Open(ctx, cfg)
	if err == nil {
		t.Fatal("second Open() error = nil, want compatibility error")
	}

	var storeErr *persistence.Error
	if !errors.As(err, &storeErr) {
		t.Fatalf("second Open() error type = %T, want *persistence.Error", err)
	}
	if storeErr.Code != persistence.CodeUnsupportedSchemaVersion {
		t.Fatalf(
			"second Open() error code = %q, want %q",
			storeErr.Code,
			persistence.CodeUnsupportedSchemaVersion,
		)
	}

	db, err := sql.Open("sqlite3", path)
	if err != nil {
		t.Fatalf("open sqlite file for verification: %v", err)
	}
	defer func() {
		_ = db.Close()
	}()

	snapshot := loadInstallationMetadata(t, db)
	if snapshot.DatabaseFormatVersion != 9999 {
		t.Fatalf("database_format_version = %d, want 9999", snapshot.DatabaseFormatVersion)
	}
}

func TestOpenFailsOnSchemaCompatibilityMajorMismatch(t *testing.T) {
	ctx := context.Background()
	path := filepath.Join(t.TempDir(), "kiln.db")
	cfg := testConfig(path)

	store, err := persistence.Open(ctx, cfg)
	if err != nil {
		t.Fatalf("first Open(): %v", err)
	}
	if _, err := store.GetDB().Exec(`
		UPDATE installation_metadata
		SET schema_compatibility_major = schema_compatibility_major + 1
		WHERE singleton_key = 1
	`); err != nil {
		t.Fatalf("seed schema compatibility mismatch: %v", err)
	}
	if err := store.Close(); err != nil {
		t.Fatalf("first Close(): %v", err)
	}

	_, err = persistence.Open(ctx, cfg)
	if err == nil {
		t.Fatal("second Open() error = nil, want compatibility error")
	}

	var storeErr *persistence.Error
	if !errors.As(err, &storeErr) {
		t.Fatalf("second Open() error type = %T, want *persistence.Error", err)
	}
	if storeErr.Code != persistence.CodeUnsupportedSchemaVersion {
		t.Fatalf(
			"second Open() error code = %q, want %q",
			storeErr.Code,
			persistence.CodeUnsupportedSchemaVersion,
		)
	}
}

func TestOpenDoesNotRewriteDatabaseFormatWithoutMigrationChange(t *testing.T) {
	ctx := context.Background()
	path := filepath.Join(t.TempDir(), "kiln.db")
	cfg := testConfig(path)

	first, err := persistence.Open(ctx, cfg)
	if err != nil {
		t.Fatalf("first Open(): %v", err)
	}
	if _, err := first.GetDB().Exec(`
		UPDATE installation_metadata
		SET database_format_version = 1
		WHERE singleton_key = 1
	`); err != nil {
		t.Fatalf("seed database format version: %v", err)
	}
	if err := first.Close(); err != nil {
		t.Fatalf("first Close(): %v", err)
	}

	second, err := persistence.Open(ctx, cfg)
	if err != nil {
		t.Fatalf("second Open(): %v", err)
	}
	defer func() {
		_ = second.Close()
	}()

	snapshot := loadInstallationMetadata(t, second.GetDB())
	if snapshot.DatabaseFormatVersion != 1 {
		t.Fatalf("database_format_version = %d, want 1", snapshot.DatabaseFormatVersion)
	}
}

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
			input:     "relative/db",
			wantError: true,
		},
		{
			name:      "non db extension",
			input:     "/tmp/sqlite",
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
				var storeErr *persistence.Error
				if !errors.As(err, &storeErr) {
					t.Fatalf("validateStorePath(%q) error type = %T, want *Error", tt.input, err)
				}
				if storeErr.Code != persistence.CodeInvalidPath {
					t.Fatalf(
						"validateStorePath(%q) error code = %q, want %q",
						tt.input,
						storeErr.Code,
						persistence.CodeInvalidPath,
					)
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

func validateStorePath(path string) (validated *string, err error) {
	if len(path) == 0 {
		return nil, persistence.NewStoreError(
			path,
			persistence.CodeInvalidPath,
			runtime_error.ErrorKilnErrorCategoryValidation,
			"store path must be provided",
			false,
			nil,
		)
	}
	cleaned := filepath.Clean(path)
	if cleaned == ":memory:" {
		return &cleaned, nil
	}
	if !filepath.IsAbs(cleaned) {
		return nil, persistence.NewStoreError(
			path,
			persistence.CodeInvalidPath,
			runtime_error.ErrorKilnErrorCategoryValidation,
			"provided store path must be an absolute path",
			false,
			nil,
		)
	}
	if !strings.HasSuffix(cleaned, ".db") {
		return nil, persistence.NewStoreError(
			path,
			persistence.CodeInvalidPath,
			runtime_error.ErrorKilnErrorCategoryValidation,
			"provided store path must be a .db file",
			false,
			nil,
		)
	}
	return &cleaned, nil
}

func testConfig(path string) persistence.Config {
	return persistence.Config{
		DBType:             persistence.StoreKindSqlite,
		InstallationDBPath: path,
		MaxOpenConnections: 1,
		MaxIdleConnections: 1,
	}
}
