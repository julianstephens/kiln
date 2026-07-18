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

var ErrInstallationIDEmpty = errors.New("installation ID must be set")

const TableNameInstallationMetadata = "installation_metadata"

type MaintenanceState string

const (
	MaintenanceStateNormal            MaintenanceState = "normal"
	MaintenanceStateMigrationRequired MaintenanceState = "migration_required"
	MaintenanceStateMigrationFailed   MaintenanceState = "migration_failed"
	MaintenanceStateMaintenance       MaintenanceState = "maintenance"
	MaintenanceStateReadOnly          MaintenanceState = "read_only"
)

type InstallationMetadataTable struct {
	executor *table.Executor
}

func (t *InstallationMetadataTable) SetExecutor(executor *table.Executor) {
	t.executor = executor
}

// TableName returns the name of the installation metadata table.
func (t *InstallationMetadataTable) TableName() string {
	return TableNameInstallationMetadata
}

// Exists checks if the installation metadata table exists in the database. Returns true if it exists, false otherwise.
func (t *InstallationMetadataTable) Exists(ctx context.Context) (bool, error) {
	ctx, cancel := context.WithTimeout(ctx, table.DefaultQueryTimeout*time.Second)
	defer cancel()

	var count int
	row, err := t.executor.QueryRowContext(
		ctx,
		`SELECT count(*) FROM sqlite_schema WHERE type='table' AND name=?`,
		[]any{TableNameInstallationMetadata},
	)
	if err != nil {
		return false, err
	}
	err = row.Scan(&count)
	if err != nil {
		return false, err
	}
	return count > 0, nil
}

type InstallationMetadataRow struct {
	executor                 *table.Executor  `json:"-"`
	SingletonKey             int              `json:"singleton_key"`
	InstallationID           string           `json:"installation_id"`
	DatabaseFormatVersion    int64            `json:"database_format_version"`
	SchemaCompatibilityMajor int              `json:"schema_compatibility_major"`
	MinimumRuntimeVersion    string           `json:"minimum_runtime_version"`
	LastOpenedRuntimeVersion string           `json:"last_opened_runtime_version"`
	MaintenanceState         MaintenanceState `json:"maintenance_state"`
	MaintenanceDetailsJSON   string           `json:"maintenance_details_json"`
	CreatedAt                int64            `json:"created_at"`
	UpdatedAt                int64            `json:"updated_at"`
}

type InstallationMetadataRowUpdater struct {
	DatabaseFormatVersion    *int64            `json:"database_format_version,omitempty"`
	SchemaCompatibilityMajor *int              `json:"schema_compatibility_major,omitempty"`
	MinimumRuntimeVersion    *string           `json:"minimum_runtime_version,omitempty"`
	LastOpenedRuntimeVersion *string           `json:"last_opened_runtime_version,omitempty"`
	MaintenanceState         *MaintenanceState `json:"maintenance_state,omitempty"`
	MaintenanceDetailsJSON   *string           `json:"maintenance_details_json,omitempty"`
}

func (m *InstallationMetadataRow) SetExecutor(executor *table.Executor) {
	m.executor = executor
}

func (m *InstallationMetadataRow) TableName() string {
	return TableNameInstallationMetadata
}

// Load retrieves the first record from the installation metadata table into the struct.
func (m *InstallationMetadataRow) Load(ctx context.Context) (bool, error) {
	if m.InstallationID == "" {
		return false, ErrInstallationIDEmpty
	}

	ctx, cancel := context.WithTimeout(ctx, table.DefaultQueryTimeout*time.Second)
	defer cancel()

	row, err := m.executor.QueryRowContext(
		ctx,
		"SELECT * FROM "+TableNameInstallationMetadata+" WHERE installation_id = ?;",
		[]any{m.InstallationID},
	)
	if err != nil {
		return false, err
	}

	if err := row.Scan(
		&m.SingletonKey,
		&m.InstallationID,
		&m.DatabaseFormatVersion,
		&m.SchemaCompatibilityMajor,
		&m.MinimumRuntimeVersion,
		&m.LastOpenedRuntimeVersion,
		&m.MaintenanceState,
		&m.MaintenanceDetailsJSON,
		&m.CreatedAt,
		&m.UpdatedAt,
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
func (m *InstallationMetadataRow) LoadFirst(ctx context.Context) (bool, error) {
	ctx, cancel := context.WithTimeout(ctx, table.DefaultQueryTimeout*time.Second)
	defer cancel()

	row, err := m.executor.QueryRowContext(ctx, "SELECT * FROM "+TableNameInstallationMetadata+" LIMIT 1;", []any{})
	if err != nil {
		return false, err
	}
	if err := row.Scan(
		&m.SingletonKey,
		&m.InstallationID,
		&m.DatabaseFormatVersion,
		&m.SchemaCompatibilityMajor,
		&m.MinimumRuntimeVersion,
		&m.LastOpenedRuntimeVersion,
		&m.MaintenanceState,
		&m.MaintenanceDetailsJSON,
		&m.CreatedAt,
		&m.UpdatedAt,
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
func (m *InstallationMetadataRow) Insert(ctx context.Context) error {
	if m.DatabaseFormatVersion == 0 {
		return errors.New("database format version must be set")
	}
	if m.MaintenanceState == "" {
		m.MaintenanceState = MaintenanceStateNormal
	}
	m.SingletonKey = 1
	m.InstallationID = ulid.Make().String()
	m.SchemaCompatibilityMajor = schema.CompatibilityMajor
	m.LastOpenedRuntimeVersion = util.RuntimeProtocolVersion
	m.MinimumRuntimeVersion = util.RuntimeProtocolVersion

	ctx, cancel := context.WithTimeout(ctx, table.DefaultQueryTimeout*time.Second)
	defer cancel()

	_, err := m.executor.ExecContext(
		ctx,
		`INSERT INTO `+TableNameInstallationMetadata+` (
			singleton_key,
			installation_id,
			database_format_version,
			schema_compatibility_major,
			minimum_runtime_version,
			last_opened_runtime_version,
			maintenance_state,
			maintenance_details_json
		) VALUES (?, ?, ?, ?, ?, ?, ?, ?);
		`,
		[]any{
			m.SingletonKey,
			m.InstallationID,
			m.DatabaseFormatVersion,
			m.SchemaCompatibilityMajor,
			m.MinimumRuntimeVersion,
			m.LastOpenedRuntimeVersion,
			m.MaintenanceState,
			m.MaintenanceDetailsJSON,
		},
	)
	return err
}

// Update modifies the existing record for the installation metadata table in the database.
func (m *InstallationMetadataRow) Update(ctx context.Context, updates InstallationMetadataRowUpdater) (int64, error) {
	id := m.InstallationID
	if id == "" {
		return 0, ErrInstallationIDEmpty
	}

	storedMetadata := &InstallationMetadataRow{InstallationID: id}
	storedMetadata.SetExecutor(m.executor)
	rowExists, err := storedMetadata.Load(ctx)
	if err != nil {
		return 0, err
	}
	if !rowExists {
		return 0, sql.ErrNoRows
	}

	m.DatabaseFormatVersion = storedMetadata.DatabaseFormatVersion
	if updates.DatabaseFormatVersion != nil {
		m.DatabaseFormatVersion = *updates.DatabaseFormatVersion
	}
	m.SchemaCompatibilityMajor = storedMetadata.SchemaCompatibilityMajor
	if updates.SchemaCompatibilityMajor != nil {
		m.SchemaCompatibilityMajor = *updates.SchemaCompatibilityMajor
	}
	m.MinimumRuntimeVersion = storedMetadata.MinimumRuntimeVersion
	if updates.MinimumRuntimeVersion != nil {
		m.MinimumRuntimeVersion = *updates.MinimumRuntimeVersion
	}
	m.LastOpenedRuntimeVersion = storedMetadata.LastOpenedRuntimeVersion
	if updates.LastOpenedRuntimeVersion != nil {
		m.LastOpenedRuntimeVersion = *updates.LastOpenedRuntimeVersion
	}
	m.MaintenanceState = storedMetadata.MaintenanceState
	if updates.MaintenanceState != nil {
		m.MaintenanceState = *updates.MaintenanceState
	}
	m.MaintenanceDetailsJSON = storedMetadata.MaintenanceDetailsJSON
	if updates.MaintenanceDetailsJSON != nil {
		m.MaintenanceDetailsJSON = *updates.MaintenanceDetailsJSON
	}

	ctx, cancel := context.WithTimeout(ctx, table.DefaultQueryTimeout*time.Second)
	defer cancel()

	res, err := m.executor.ExecContext(
		ctx,
		`UPDATE `+TableNameInstallationMetadata+` SET
			database_format_version = ?,
			schema_compatibility_major = ?,
			minimum_runtime_version = ?,
			last_opened_runtime_version = ?,
			maintenance_state = ?,
			maintenance_details_json = ?,
			updated_at = unixepoch()
		WHERE installation_id = ?;
		`,
		[]any{
			m.DatabaseFormatVersion,
			m.SchemaCompatibilityMajor,
			m.MinimumRuntimeVersion,
			m.LastOpenedRuntimeVersion,
			m.MaintenanceState,
			m.MaintenanceDetailsJSON,
			m.InstallationID,
		},
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
func (m *InstallationMetadataRow) Delete(ctx context.Context) (int64, error) {
	if m.InstallationID == "" {
		return 0, ErrInstallationIDEmpty
	}

	rowExists, err := m.Load(ctx)
	if err != nil {
		return 0, err
	}
	if !rowExists {
		return 0, errors.New("installation metadata record does not exist")
	}

	res, err := m.executor.ExecContext(
		ctx,
		"DELETE FROM "+TableNameInstallationMetadata+" WHERE installation_id = ?;",
		[]any{m.InstallationID},
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
