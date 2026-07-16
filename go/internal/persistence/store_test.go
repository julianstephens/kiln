package persistence_test

import (
	"context"
	"errors"
	"path/filepath"
	"strings"
	"testing"

	"github.com/julianstephens/kiln/go/internal/persistence"
	runtime_error "github.com/julianstephens/kiln/go/schema/runtime/error"
	_ "github.com/mattn/go-sqlite3"
)

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
