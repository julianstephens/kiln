package installation_test

import (
	"context"
	"database/sql"
	"testing"

	"github.com/julianstephens/kiln/go/internal/persistence/table/installation"
	"github.com/julianstephens/kiln/go/internal/util"
	"github.com/julianstephens/kiln/go/schema"
	_ "github.com/mattn/go-sqlite3"
)

func openInMemoryDB(t *testing.T) *sql.DB {
	t.Helper()
	db, err := sql.Open("sqlite3", ":memory:")
	if err != nil {
		t.Fatalf("failed to open in-memory sqlite database: %v", err)
	}
	t.Cleanup(func() { _ = db.Close() })
	return db
}

func createInstallationTable(t *testing.T, db *sql.DB) {
	t.Helper()
	_, err := db.Exec(`
		CREATE TABLE installation_metadata (
			installation_id TEXT NOT NULL,
			database_format_version INTEGER NOT NULL,
			schema_compatibility_major INTEGER NOT NULL,
			minimum_runtime_version TEXT,
			last_opened_runtime_version TEXT,
			maintenance_state TEXT NOT NULL
		);
	`)
	if err != nil {
		t.Fatalf("failed to create installation_metadata table: %v", err)
	}
}

func TestInstallationMetadata_Insert(t *testing.T) {
	t.Parallel()

	t.Run("inserts row with correct values", func(t *testing.T) {
		t.Parallel()

		db := openInMemoryDB(t)
		createInstallationTable(t, db)

		m := &installation.InstallationMetadataRow{
			DatabaseFormatVersion: 1,
			MaintenanceState:      installation.MaintenanceStateNormal,
		}
		err := m.Insert(context.Background(), db)
		if err != nil {
			t.Fatalf("Insert returned unexpected error: %v", err)
		}

		var count int
		var installationID string
		var dbFormatVersion int64
		var compatibilityMajor int
		var minVersion, lastOpenedVersion, maintenanceState string
		if err := db.QueryRow(`
			SELECT COUNT(*), installation_id, database_format_version, schema_compatibility_major,
			       minimum_runtime_version, last_opened_runtime_version, maintenance_state
			FROM installation_metadata;
		`).Scan(&count, &installationID, &dbFormatVersion, &compatibilityMajor,
			&minVersion, &lastOpenedVersion, &maintenanceState); err != nil {
			t.Fatalf("failed to read inserted row: %v", err)
		}

		if count != 1 {
			t.Fatalf("row count = %d, want 1", count)
		}
		if installationID == "" {
			t.Fatal("installation_id is empty, want a ULID")
		}
		if dbFormatVersion != 1 {
			t.Fatalf("database_format_version = %d, want 1", dbFormatVersion)
		}
		if compatibilityMajor != schema.CompatibilityMajor {
			t.Fatalf("schema_compatibility_major = %d, want %d", compatibilityMajor, schema.CompatibilityMajor)
		}
		if minVersion != util.RuntimeProtocolVersion {
			t.Fatalf("minimum_runtime_version = %q, want %q", minVersion, util.RuntimeProtocolVersion)
		}
		if lastOpenedVersion != util.RuntimeProtocolVersion {
			t.Fatalf("last_opened_runtime_version = %q, want %q", lastOpenedVersion, util.RuntimeProtocolVersion)
		}
		if maintenanceState != string(installation.MaintenanceStateNormal) {
			t.Fatalf("maintenance_state = %q, want %q", maintenanceState, installation.MaintenanceStateNormal)
		}
	})

	t.Run("returns error when table does not exist", func(t *testing.T) {
		t.Parallel()

		db := openInMemoryDB(t)
		m := &installation.InstallationMetadataRow{
			DatabaseFormatVersion: 1,
			MaintenanceState:      installation.MaintenanceStateNormal,
		}
		err := m.Insert(context.Background(), db)
		if err == nil {
			t.Fatal("Insert error = nil, want error")
		}
	})
}

func TestInstallationMetadata_Load(t *testing.T) {
	t.Parallel()

	t.Run("returns nil and leaves struct zero-valued when table is empty", func(t *testing.T) {
		t.Parallel()

		db := openInMemoryDB(t)
		createInstallationTable(t, db)

		m := &installation.InstallationMetadataRow{}
		exists, err := m.LoadFirst(context.Background(), db)
		if err != nil {
			t.Fatalf("LoadFirst returned unexpected error: %v", err)
		}
		if exists {
			t.Fatal("expected exists=false when table is empty, got true")
		}
		if m.InstallationID != "" {
			t.Fatalf("InstallationID = %q, want empty string", m.InstallationID)
		}
	})

	t.Run("populates struct from existing row", func(t *testing.T) {
		t.Parallel()

		db := openInMemoryDB(t)
		createInstallationTable(t, db)

		const wantID = "01ARZ3NDEKTSV4RRFFQ69G5FAV"
		_, err := db.Exec(`
			INSERT INTO installation_metadata (
				installation_id, database_format_version, schema_compatibility_major,
				minimum_runtime_version, last_opened_runtime_version, maintenance_state
			) VALUES (?, ?, ?, ?, ?, ?);
		`, wantID, int64(2), schema.CompatibilityMajor,
			util.RuntimeProtocolVersion, util.RuntimeProtocolVersion,
			string(installation.MaintenanceStateMaintenance))
		if err != nil {
			t.Fatalf("failed to seed row: %v", err)
		}

		m := &installation.InstallationMetadataRow{}
		exists, err := m.LoadFirst(context.Background(), db)
		if err != nil {
			t.Fatalf("LoadFirst returned unexpected error: %v", err)
		}
		if !exists {
			t.Fatal("expected exists=true when table has a row, got false")
		}

		if m.InstallationID != wantID {
			t.Fatalf("InstallationID = %q, want %q", m.InstallationID, wantID)
		}
		if m.DatabaseFormatVersion != 2 {
			t.Fatalf("DatabaseFormatVersion = %d, want 2", m.DatabaseFormatVersion)
		}
		if m.SchemaCompatibilityMajor != schema.CompatibilityMajor {
			t.Fatalf("SchemaCompatibilityMajor = %d, want %d", m.SchemaCompatibilityMajor, schema.CompatibilityMajor)
		}
		if m.MinimumRuntimeVersion != util.RuntimeProtocolVersion {
			t.Fatalf("MinimumRuntimeVersion = %q, want %q", m.MinimumRuntimeVersion, util.RuntimeProtocolVersion)
		}
		if m.LastOpenedRuntimeVersion != util.RuntimeProtocolVersion {
			t.Fatalf("LastOpenedRuntimeVersion = %q, want %q", m.LastOpenedRuntimeVersion, util.RuntimeProtocolVersion)
		}
		if m.MaintenanceState != installation.MaintenanceStateMaintenance {
			t.Fatalf("MaintenanceState = %q, want %q", m.MaintenanceState, installation.MaintenanceStateMaintenance)
		}
	})

	t.Run("returns error when table does not exist", func(t *testing.T) {
		t.Parallel()

		db := openInMemoryDB(t)
		m := &installation.InstallationMetadataRow{}
		exists, err := m.LoadFirst(context.Background(), db)
		if err == nil {
			t.Fatal("LoadFirst error = nil, want error")
		}
		if exists {
			t.Fatal("expected exists=false when table does not exist, got true")
		}
	})
}
