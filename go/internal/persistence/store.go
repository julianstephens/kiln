package persistence

import (
	"context"
	"database/sql"
	"errors"
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"time"

	"github.com/julianstephens/kiln/go/internal/persistence/table"
	"github.com/julianstephens/kiln/go/internal/persistence/table/installation"
	"github.com/julianstephens/kiln/go/internal/util"
	runtime_error "github.com/julianstephens/kiln/go/schema/runtime/error"
	"github.com/rogpeppe/go-internal/lockedfile"

	_ "github.com/mattn/go-sqlite3"
	_ "turso.tech/database/tursogo"
)

type Config struct {
	DBType                       StoreKind `json:"db_type"`
	InstallationDBPath           string    `json:"installation_db_path"`
	MaxOpenConnections           int       `json:"max_open_connections"`
	MaxIdleConnections           int       `json:"max_idle_connections"`
	MaxConnectionLifetimeSeconds int       `json:"max_connection_lifetime_seconds"`
}

type Store interface {
	Close() error
	Health(ctx context.Context) error
	GetDB() *sql.DB
}

type StoreKind string

const (
	StoreKindTurso  StoreKind = "turso"
	StoreKindSqlite StoreKind = "sqlite3"
)

const (
	LockDir = "locks"
)

// Open opens a new Store based on the provided kind and path.
func Open(ctx context.Context, cfg Config) (Store, error) {
	validatedPath, err := validateStorePath(cfg.InstallationDBPath)
	if err != nil {
		return nil, err
	}

	installationDir := filepath.Dir(*validatedPath)
	if err := ensureDirectoryExists(installationDir); err != nil {
		return nil, NewStoreError(
			*validatedPath,
			CodeStoreInitializationFailed,
			runtime_error.ErrorKilnErrorCategoryInternal,
			"failed to ensure installation directory exists",
			false,
			err,
		)
	}

	dsn := fmt.Sprintf(
		"file:%s?_journal_mode=WAL&_synchronous=NORMAL&_foreign_keys=ON&_cache_size=-202000000&_busy_timeout=5000&_optimize",
		*validatedPath,
	)

	conn, err := sql.Open(string(cfg.DBType), dsn)
	if err != nil {
		return nil, NewStoreOpenFailedError(*validatedPath, err)
	}
	opened := false
	defer func() {
		if !opened {
			_ = conn.Close()
		}
	}()

	conn.SetMaxOpenConns(cfg.MaxOpenConnections)
	conn.SetMaxIdleConns(cfg.MaxIdleConnections)
	conn.SetConnMaxLifetime(time.Duration(cfg.MaxConnectionLifetimeSeconds) * time.Second)

	var store Store
	switch cfg.DBType {
	case StoreKindTurso:
		store = &TursoStore{
			Path: cfg.InstallationDBPath,
			Conn: conn,
		}
	case StoreKindSqlite:
		store = &SqliteStore{
			Path: cfg.InstallationDBPath,
			Conn: conn,
		}
	default:
		return nil, NewStoreNotFoundError(cfg.InstallationDBPath)
	}

	if err := store.Health(ctx); err != nil {
		return nil, err
	}

	// skip lockfile creation for in-memory databases, as they are not shared between processes
	if cfg.InstallationDBPath != ":memory:" {
		lockDir := filepath.Join(filepath.Dir(cfg.InstallationDBPath), LockDir)
		if err := ensureDirectoryExists(lockDir); err != nil {
			return nil, NewStoreError(
				cfg.InstallationDBPath,
				CodeStoreInitializationFailed,
				runtime_error.ErrorKilnErrorCategoryInternal,
				"failed to ensure lock directory exists",
				false,
				err,
			)
		}
		lockfilePath := filepath.Join(lockDir, "migration.lock")
		unlock, err := lockedfile.MutexAt(lockfilePath).Lock()
		if err != nil {
			return nil, NewMigrationLockFailedError(cfg.InstallationDBPath, err)
		}
		defer unlock()
	}

	latestSupportedVersion, err := latestEmbeddedMigrationVersion()
	if err != nil {
		if !errors.Is(err, sql.ErrNoRows) {
			return nil, NewMigrationFailedError(cfg.InstallationDBPath, err)
		}
	}
	schemaVersion, err := currentDBVersion(ctx, store.GetDB())
	if err != nil {
		if !errors.Is(err, sql.ErrNoRows) {
			return nil, NewMigrationFailedError(cfg.InstallationDBPath, err)
		}
	}
	if schemaVersion > 0 && schemaVersion > latestSupportedVersion {
		return nil, NewSchemaVersionMismatchError(
			cfg.InstallationDBPath,
			schemaVersion,
			latestSupportedVersion,
		)
	}

	migrationErr := migrate(ctx, store.GetDB())
	if migrationErr != nil {
		bestEffortRecordMigrationFailure(ctx, store.GetDB())
		return nil, NewMigrationFailedError(cfg.InstallationDBPath, migrationErr)
	}

	if _, err := loadOrCreateInstallationMetadata(ctx, store.GetDB(), latestSupportedVersion); err != nil {
		return nil, NewStoreError(
			cfg.InstallationDBPath,
			CodeStoreInitializationFailed,
			runtime_error.ErrorKilnErrorCategoryInternal,
			"failed to load or create installation metadata",
			false,
			err,
		)
	}

	opened = true
	return store, nil
}

// TursoStore represents a Turso database store.
type TursoStore struct {
	Path string
	Conn *sql.DB
}

// Close closes the TursoStore connection.
func (t *TursoStore) Close() error {
	if err := t.Conn.Close(); err != nil {
		return NewStoreCloseFailedError(t.Path, err)
	}
	return nil
}

// Health checks the health of the TursoStore by pinging the database.
func (t *TursoStore) Health(ctx context.Context) error {
	cancelCtx, cancel := context.WithTimeout(ctx, 2*time.Second)
	defer cancel()

	if err := t.Conn.PingContext(cancelCtx); err != nil {
		return NewHealthCheckFailedError(t.Path, err)
	}
	return nil
}

// GetDB returns the underlying sql.DB connection of the TursoStore.
func (t *TursoStore) GetDB() *sql.DB {
	return t.Conn
}

// SqliteStore represents a SQLite database store.
type SqliteStore struct {
	Path string
	Conn *sql.DB
}

// Close closes the SqliteStore connection.
func (s *SqliteStore) Close() error {
	if err := s.Conn.Close(); err != nil {
		return NewStoreCloseFailedError(s.Path, err)
	}
	return nil
}

// Health checks the health of the SqliteStore by pinging the database.
func (s *SqliteStore) Health(ctx context.Context) error {
	cancelCtx, cancel := context.WithTimeout(ctx, 2*time.Second)
	defer cancel()

	if err := s.Conn.PingContext(cancelCtx); err != nil {
		return NewHealthCheckFailedError(s.Path, err)
	}
	return nil
}

// GetDB returns the underlying sql.DB connection of the SqliteStore.
func (s *SqliteStore) GetDB() *sql.DB {
	return s.Conn
}

func validateStorePath(path string) (validated *string, err error) {
	if len(path) == 0 {
		return nil, NewStoreError(
			path,
			CodeInvalidPath,
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
		return nil, NewStoreError(
			path,
			CodeInvalidPath,
			runtime_error.ErrorKilnErrorCategoryValidation,
			"provided store path must be an absolute path",
			false,
			nil,
		)
	}
	if !strings.HasSuffix(cleaned, ".db") {
		return nil, NewStoreError(
			path,
			CodeInvalidPath,
			runtime_error.ErrorKilnErrorCategoryValidation,
			"provided store path must be a .db file",
			false,
			nil,
		)
	}
	return &cleaned, nil
}

func bestEffortRecordMigrationFailure(ctx context.Context, db *sql.DB) {
	metadataTable := &installation.InstallationMetadataTable{}
	installationMetadata := &installation.InstallationMetadataRow{}

	txn, err := db.BeginTx(ctx, nil)
	if err != nil {
		return
	}
	defer func() {
		_ = txn.Rollback()
	}()

	metadataTable.SetExecutor(table.NewExecutorWithTx(txn))
	installationMetadata.SetExecutor(table.NewExecutorWithTx(txn))

	exists, err := metadataTable.Exists(ctx)
	if err != nil || !exists {
		return
	}

	exists, err = installationMetadata.LoadFirst(ctx)
	if err != nil || !exists {
		return
	}
	installationMetadata.MaintenanceState = installation.MaintenanceStateMigrationFailed
	installationMetadata.LastOpenedRuntimeVersion = util.RuntimeProtocolVersion

	if _, err = installationMetadata.Update(ctx); err != nil {
		return
	}

	_ = txn.Commit()
}

func loadOrCreateInstallationMetadata(
	ctx context.Context,
	db *sql.DB,
	dbFormatVersion int64,
) (installationID string, err error) {
	installationMetadata := &installation.InstallationMetadataRow{DatabaseFormatVersion: dbFormatVersion}
	txn, txErr := db.BeginTx(ctx, nil)
	if txErr != nil {
		err = fmt.Errorf("begin installation metadata transaction: %w", txErr)
		return
	}
	defer func() {
		if err == nil {
			return
		}

		if rollbackErr := txn.Rollback(); rollbackErr != nil {
			err = errors.Join(err, fmt.Errorf("rollback installation metadata transaction: %w", rollbackErr))
		}
	}()
	installationMetadata.SetExecutor(table.NewExecutorWithTx(txn))

	exists, loadErr := installationMetadata.LoadFirst(ctx)
	if loadErr != nil {
		err = fmt.Errorf("load installation metadata: %w", loadErr)
		return
	}

	if exists {
		if installationMetadata.InstallationID == "" {
			err = errors.New("installation metadata record exists but installation ID is empty")
			return
		}

		installationMetadata.LastOpenedRuntimeVersion = util.RuntimeProtocolVersion

		if _, updateErr := installationMetadata.Update(ctx); updateErr != nil {
			err = fmt.Errorf("update installation metadata: %w", updateErr)
			return
		}

		if commitErr := txn.Commit(); commitErr != nil {
			err = fmt.Errorf("commit installation metadata transaction: %w", commitErr)
			return
		}

		installationID = installationMetadata.InstallationID
		return
	}

	insertErr := installationMetadata.Insert(ctx)
	if insertErr != nil {
		err = fmt.Errorf("insert installation metadata: %w", insertErr)
		return
	}

	if commitErr := txn.Commit(); commitErr != nil {
		err = fmt.Errorf("commit installation metadata transaction: %w", commitErr)
		return
	}

	installationID = installationMetadata.InstallationID
	return
}

func ensureDirectoryExists(path string) error {
	if _, err := os.Stat(path); os.IsNotExist(err) {
		if mkdirErr := os.MkdirAll(path, 0o750); mkdirErr != nil {
			return fmt.Errorf("ensure directory exists: %w", mkdirErr)
		}
	}
	return nil
}
