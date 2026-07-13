package installation

import (
	"context"
	"database/sql"
	"errors"
	"time"

	"github.com/julianstephens/kiln/go/internal/persistence/table"
	"github.com/julianstephens/kiln/go/internal/util"
	"github.com/julianstephens/kiln/go/schema"
	"github.com/oklog/ulid/v2"
)

const TableNameInstallationMetadata = "installation_metadata"

type MaintenanceState string

const (
	MaintenanceStateNormal            MaintenanceState = "normal"
	MaintenanceStateMigrationRequired MaintenanceState = "migration_required"
	MaintenanceStateMigrationFailed   MaintenanceState = "migration_failed"
	MaintenanceStateMaintenance       MaintenanceState = "maintenance"
	MaintenanceStateReadOnly          MaintenanceState = "read_only"
)

type InstallationMetadataTable struct{}

type InstallationMetadataRow struct {
	InstallationID           string           `json:"installation_id"`
	DatabaseFormatVersion    int64            `json:"database_format_version"`
	SchemaCompatibilityMajor int              `json:"schema_compatibility_major"`
	MinimumRuntimeVersion    string           `json:"minimum_runtime_version"`
	LastOpenedRuntimeVersion string           `json:"last_opened_runtime_version"`
	MaintenanceState         MaintenanceState `json:"maintenance_state"`
}

var ErrInstallationIDEmpty = errors.New("installation ID must be set")

// TableName returns the name of the installation metadata table.
func (t *InstallationMetadataTable) TableName() string {
	return TableNameInstallationMetadata
}

// Exists checks if the installation metadata table exists in the database. Returns true if it exists, false otherwise.
func (t *InstallationMetadataTable) Exists(ctx context.Context, db *sql.DB) (bool, error) {
	ctx, cancel := context.WithTimeout(ctx, table.DefaultQueryTimeout*time.Second)
	defer cancel()

	var count int
	row := db.QueryRowContext(
		ctx,
		`SELECT count(*) FROM sqlite_schema WHERE type='table' AND name=?`,
		TableNameInstallationMetadata,
	)
	err := row.Scan(&count)
	if err != nil {
		return false, err
	}
	return count > 0, nil
}

func (m *InstallationMetadataRow) TableName() string {
	return TableNameInstallationMetadata
}

// Load retrieves the first record from the installation metadata table into the struct.
func (m *InstallationMetadataRow) Load(ctx context.Context, db *sql.DB) (bool, error) {
	if m.InstallationID == "" {
		return false, ErrInstallationIDEmpty
	}

	ctx, cancel := context.WithTimeout(ctx, table.DefaultQueryTimeout*time.Second)
	defer cancel()

	row := db.QueryRowContext(
		ctx,
		"SELECT * FROM "+TableNameInstallationMetadata+" WHERE installation_id = ?;",
		m.InstallationID,
	)
	if err := row.Scan(
		&m.InstallationID,
		&m.DatabaseFormatVersion,
		&m.SchemaCompatibilityMajor,
		&m.MinimumRuntimeVersion,
		&m.LastOpenedRuntimeVersion,
		&m.MaintenanceState,
	); err != nil {
		if errors.Is(err, sql.ErrNoRows) {
			return false, nil
		} else {
			return false, err
		}
	}
	return true, nil
}

// LoadFirst retrieves the first record from the installation metadata table into the struct.
func (m *InstallationMetadataRow) LoadFirst(ctx context.Context, db *sql.DB) (bool, error) {
	ctx, cancel := context.WithTimeout(ctx, table.DefaultQueryTimeout*time.Second)
	defer cancel()

	row := db.QueryRowContext(ctx, "SELECT * FROM "+TableNameInstallationMetadata+" LIMIT 1;")
	if err := row.Scan(
		&m.InstallationID,
		&m.DatabaseFormatVersion,
		&m.SchemaCompatibilityMajor,
		&m.MinimumRuntimeVersion,
		&m.LastOpenedRuntimeVersion,
		&m.MaintenanceState,
	); err != nil {
		if errors.Is(err, sql.ErrNoRows) {
			return false, nil
		} else {
			return false, err
		}
	}
	return true, nil
}

// Insert adds a new record for the installation metadata table in the database.
func (m *InstallationMetadataRow) Insert(ctx context.Context, db *sql.DB) error {
	if m.DatabaseFormatVersion == 0 {
		return errors.New("database format version must be set")
	}
	if m.MaintenanceState == "" {
		m.MaintenanceState = MaintenanceStateNormal
	}
	m.InstallationID = ulid.Make().String()
	m.SchemaCompatibilityMajor = schema.CompatibilityMajor
	m.LastOpenedRuntimeVersion = util.RuntimeProtocolVersion
	m.MinimumRuntimeVersion = util.RuntimeProtocolVersion

	ctx, cancel := context.WithTimeout(ctx, table.DefaultQueryTimeout*time.Second)
	defer cancel()

	_, err := db.ExecContext(
		ctx,
		`INSERT INTO `+TableNameInstallationMetadata+` (
			installation_id,
			database_format_version,
			schema_compatibility_major,
			minimum_runtime_version,
			last_opened_runtime_version,
			maintenance_state
		) VALUES (?, ?, ?, ?, ?, ?);
		`,
		m.InstallationID,
		m.DatabaseFormatVersion,
		m.SchemaCompatibilityMajor,
		m.MinimumRuntimeVersion,
		m.LastOpenedRuntimeVersion,
		m.MaintenanceState,
	)
	return err
}

// Update modifies the existing record for the installation metadata table in the database.
func (m *InstallationMetadataRow) Update(ctx context.Context, db *sql.DB) (int64, error) {
	id := m.InstallationID
	if id == "" {
		return 0, ErrInstallationIDEmpty
	}

	storedMetadata := &InstallationMetadataRow{InstallationID: id}
	rowExists, err := storedMetadata.Load(ctx, db)
	if !rowExists || err != nil {
		return 0, err
	}

	if !table.IsSet(&m.DatabaseFormatVersion) {
		m.DatabaseFormatVersion = storedMetadata.DatabaseFormatVersion
	}
	if !table.IsSet(&m.SchemaCompatibilityMajor) {
		m.SchemaCompatibilityMajor = storedMetadata.SchemaCompatibilityMajor
	}
	if !table.IsSet(&m.MinimumRuntimeVersion) {
		m.MinimumRuntimeVersion = storedMetadata.MinimumRuntimeVersion
	}
	if !table.IsSet(&m.LastOpenedRuntimeVersion) {
		m.LastOpenedRuntimeVersion = util.RuntimeProtocolVersion
	}
	if !table.IsSet(&m.MaintenanceState) {
		m.MaintenanceState = storedMetadata.MaintenanceState
	}

	ctx, cancel := context.WithTimeout(ctx, table.DefaultQueryTimeout*time.Second)
	defer cancel()

	res, err := db.ExecContext(
		ctx,
		`UPDATE `+TableNameInstallationMetadata+` SET
			database_format_version = ?,
			schema_compatibility_major = ?,
			minimum_runtime_version = ?,
			last_opened_runtime_version = ?,
			maintenance_state = ?
		WHERE installation_id = ?;
		`,
		m.DatabaseFormatVersion,
		m.SchemaCompatibilityMajor,
		m.MinimumRuntimeVersion,
		m.LastOpenedRuntimeVersion,
		m.MaintenanceState,
		m.InstallationID,
	)
	if err != nil {
		return 0, err
	}
	n, err := res.RowsAffected()
	if err != nil {
		return 0, err
	}
	if n == 0 {
		return 0, sql.ErrNoRows
	}
	return n, nil
}

// Delete removes the record for the installation metadata table from the database.
func (m *InstallationMetadataRow) Delete(ctx context.Context, db *sql.DB) (int64, error) {
	if m.InstallationID == "" {
		return 0, ErrInstallationIDEmpty
	}

	rowExists, err := m.Load(ctx, db)
	if !rowExists || err != nil {
		return 0, errors.New("installation metadata record does not exist")
	}

	res, err := db.ExecContext(
		ctx,
		"DELETE FROM "+TableNameInstallationMetadata+" WHERE installation_id = ?;",
		m.InstallationID,
	)
	if err != nil {
		return 0, nil
	}
	n, err := res.RowsAffected()
	if err != nil {
		return 0, err
	}
	if n == 0 {
		return 0, sql.ErrNoRows
	}
	return n, nil
}
