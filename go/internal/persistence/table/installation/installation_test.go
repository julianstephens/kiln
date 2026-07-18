package installation_test

import (
	"context"
	"database/sql"
	"testing"

	"github.com/julianstephens/kiln/go/internal/persistence/table"
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
			singleton_key INTEGER PRIMARY KEY CHECK (singleton_key = 1),
			installation_id TEXT NOT NULL UNIQUE,
			database_format_version INTEGER NOT NULL CHECK (database_format_version >= 1),
			schema_compatibility_major INTEGER NOT NULL CHECK (schema_compatibility_major >= 1),
			minimum_runtime_version TEXT,
			last_opened_runtime_version TEXT,
			maintenance_state TEXT NOT NULL DEFAULT 'normal' CHECK (maintenance_state IN ('normal', 'migration_required', 'migration_failed', 'maintenance', 'read_only')),
			maintenance_details_json TEXT,
			created_at INTEGER NOT NULL DEFAULT (unixepoch()),
			updated_at INTEGER NOT NULL DEFAULT (unixepoch())
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
		m.SetExecutor(table.NewExecutorWithDB(db))
		err := m.Insert(context.Background())
		if err != nil {
			t.Fatalf("Insert returned unexpected error: %v", err)
		}

		var count int
		var installationID string
		var singletonKey int
		var dbFormatVersion int64
		var compatibilityMajor int
		var minVersion, lastOpenedVersion, maintenanceState string
		if err := db.QueryRow(`
			SELECT COUNT(*), singleton_key, installation_id, database_format_version, schema_compatibility_major,
			       minimum_runtime_version, last_opened_runtime_version, maintenance_state
			FROM installation_metadata;
		`).Scan(&count, &singletonKey, &installationID, &dbFormatVersion, &compatibilityMajor,
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
		m.SetExecutor(table.NewExecutorWithDB(db))
		err := m.Insert(context.Background())
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
		m.SetExecutor(table.NewExecutorWithDB(db))
		exists, err := m.LoadFirst(context.Background())
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
				singleton_key, installation_id, database_format_version, schema_compatibility_major,
				minimum_runtime_version, last_opened_runtime_version, maintenance_state, maintenance_details_json
			) VALUES (?, ?, ?, ?, ?, ?, ?, ?);
		`, int64(1), wantID, int64(2), schema.CompatibilityMajor,
			util.RuntimeProtocolVersion, util.RuntimeProtocolVersion,
			string(installation.MaintenanceStateMaintenance), "")
		if err != nil {
			t.Fatalf("failed to seed row: %v", err)
		}

		m := &installation.InstallationMetadataRow{}
		m.SetExecutor(table.NewExecutorWithDB(db))
		exists, err := m.LoadFirst(context.Background())
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
		m.SetExecutor(table.NewExecutorWithDB(db))
		exists, err := m.LoadFirst(context.Background())
		if err == nil {
			t.Fatal("LoadFirst error = nil, want error")
		}
		if exists {
			t.Fatal("expected exists=false when table does not exist, got true")
		}
	})
}

func TestInstallationMetadata_UpdateRefreshesUpdatedAt(t *testing.T) {
	t.Parallel()

	db := openInMemoryDB(t)
	createInstallationTable(t, db)

	const installationID = "01ARZ3NDEKTSV4RRFFQ69G5FAV"
	_, err := db.Exec(`
		INSERT INTO installation_metadata (
			singleton_key,
			installation_id,
			database_format_version,
			schema_compatibility_major,
			minimum_runtime_version,
			last_opened_runtime_version,
			maintenance_state,
			maintenance_details_json,
			created_at,
			updated_at
		) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
	`,
		1,
		installationID,
		int64(1),
		schema.CompatibilityMajor,
		util.RuntimeProtocolVersion,
		"old-runtime",
		string(installation.MaintenanceStateNormal),
		"",
		int64(1),
		int64(1),
	)
	if err != nil {
		t.Fatalf("failed to seed installation metadata row: %v", err)
	}

	m := &installation.InstallationMetadataRow{InstallationID: installationID}
	m.SetExecutor(table.NewExecutorWithDB(db))

	if _, err := m.Update(context.Background(), installation.InstallationMetadataRowUpdater{
		LastOpenedRuntimeVersion: table.Ptr(util.RuntimeProtocolVersion),
	}); err != nil {
		t.Fatalf("Update returned unexpected error: %v", err)
	}

	var updatedAt int64
	if err := db.QueryRow(
		"SELECT updated_at FROM installation_metadata WHERE installation_id = ?",
		installationID,
	).Scan(&updatedAt); err != nil {
		t.Fatalf("failed to load updated_at after update: %v", err)
	}

	if updatedAt <= 1 {
		t.Fatalf("updated_at = %d, want value > 1", updatedAt)
	}
}
