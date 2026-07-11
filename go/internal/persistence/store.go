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

	"github.com/julianstephens/kiln/go/internal/util"
	"github.com/julianstephens/kiln/go/schema"
	"github.com/oklog/ulid/v2"
	"github.com/rogpeppe/go-internal/lockedfile"

	_ "github.com/mattn/go-sqlite3"
	_ "turso.tech/database/tursogo"
)

const DBFormatVersion = 1

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
	TursoStoreKind  StoreKind = "turso"
	SqliteStoreKind StoreKind = "sqlite3"
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
	if _, err := ensurePath(installationDir, true); err != nil {
		return nil, NewStoreError(
			*validatedPath,
			CodeInvalidPath,
			"failed to ensure installation directory exists",
			err,
		)
	}

	exists := false
	if *validatedPath != ":memory:" {
		_, err := os.Stat(*validatedPath)
		if err != nil {
			if os.IsNotExist(err) {
				exists = false
			} else {
				return nil, NewStoreError(*validatedPath, CodeInvalidPath, "failed to stat installation path", err)
			}
		} else {
			exists = true
		}
	}

	dsn := fmt.Sprintf(
		"file:%s?_journal_mode=WAL&_synchronous=NORMAL&_foreign_keys=ON&_cache_size=-202000000&_busy_timeout=5000&_optimize",
		*validatedPath,
	)

	conn, err := sql.Open(string(cfg.DBType), dsn)
	if err != nil {
		return nil, NewStoreOpenFailedError(*validatedPath, err)
	}

	conn.SetMaxOpenConns(cfg.MaxOpenConnections)
	conn.SetMaxIdleConns(cfg.MaxIdleConnections)
	conn.SetConnMaxLifetime(time.Duration(cfg.MaxConnectionLifetimeSeconds) * time.Second)

	var store Store
	switch cfg.DBType {
	case TursoStoreKind:
		store = &TursoStore{
			Path: cfg.InstallationDBPath,
			Conn: conn,
		}
	case SqliteStoreKind:
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

	lockfilePath := filepath.Join(filepath.Dir(cfg.InstallationDBPath), LockDir, "migration.lock")
	if _, err = ensurePath(lockfilePath, false); err != nil {
		return nil, NewStoreError(*validatedPath, CodeInvalidPath, "failed to ensure locks directory exists", err)
	}
	unlock, err := lockedfile.MutexAt(lockfilePath).Lock()
	if err != nil {
		return nil, NewMigrationLockFailedError(cfg.InstallationDBPath, err)
	}
	defer unlock()

	if exists {
		schemaVersion, err := getSchemaVersion(store.GetDB())
		if err != nil {
			if !errors.Is(err, sql.ErrNoRows) {
				return nil, NewMigrationFailedError(cfg.InstallationDBPath, err)
			}
		}
		if schemaVersion > DBFormatVersion {
			return nil, NewSchemaVersionMismatchError(
				cfg.InstallationDBPath,
				schemaVersion,
				DBFormatVersion,
			)
		}
	}

	migrationErr := migrate(store.GetDB())
	var migrationState string
	if migrationErr == nil {
		migrationState = "normal"
	} else {
		migrationState = "migration_failed"
	}

	if err := updateInstallationMetadata(store.GetDB(), migrationState, exists); err != nil {
		return nil, NewStoreError(cfg.InstallationDBPath, CodeInvalidPath, "failed to initialize database", err)
	}
	if migrationErr != nil {
		return nil, NewMigrationFailedError(cfg.InstallationDBPath, migrationErr)
	}

	return store, nil
}

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

func (t *TursoStore) GetDB() *sql.DB {
	return t.Conn
}

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

func (s *SqliteStore) GetDB() *sql.DB {
	return s.Conn
}

func validateStorePath(path string) (validated *string, err error) {
	if len(path) == 0 {
		return nil, NewStoreError(path, CodeInvalidPath, "store path must be provided", nil)
	}
	cleaned := filepath.Clean(path)
	if cleaned == ":memory:" {
		return &cleaned, nil
	}
	if !filepath.IsAbs(cleaned) {
		return nil, NewStoreError(path, CodeInvalidPath, "provided store path must be an absolute path", nil)
	}
	if !strings.HasSuffix(cleaned, ".db") {
		return nil, NewStoreError(path, CodeInvalidPath, "provided store path must be a .db file", nil)
	}
	return &cleaned, nil
}

func ensurePath(path string, isDir bool) (exists bool, err error) {
	_, err = os.Stat(path)
	if err != nil && errors.Is(err, os.ErrNotExist) {
		if isDir {
			err = os.MkdirAll(path, 0o700)
		} else {
			if err := os.MkdirAll(filepath.Dir(path), 0o700); err != nil {
				return false, err
			}
			// #nosec G304 -- path is derived from validated absolute installation path and fixed lock filename
			file, err := os.OpenFile(path, os.O_CREATE, 0o600)
			if err != nil {
				return false, err
			}
			if err = file.Close(); err != nil {
				return false, err
			}
			return false, nil
		}
	}

	return err == nil, err
}

func getSchemaVersion(db *sql.DB) (int, error) {
	var version int
	row := db.QueryRow("SELECT version_id FROM goose_db_version;")
	if err := row.Scan(&version); err != nil {
		return 0, err
	}
	return version, nil
}

func updateInstallationMetadata(db *sql.DB, migrationState string, exists bool) error {
	if exists {
		var installationID string
		err := db.QueryRow("SELECT installation_id FROM installation_metadata LIMIT 1;").Scan(&installationID)
		if err != nil {
			return err
		}

		const updateInstallationSQL = `
		UPDATE installation_metadata
		SET
			database_format_version = ?,
			schema_compatibility_major = ?,
			minimum_runtime_version = ?,
			last_opened_runtime_version = ?,
			maintenance_state = ?
		WHERE installation_id = ?;
		`
		_, err = db.Exec(
			updateInstallationSQL,
			DBFormatVersion,
			schema.CompatibilityMajor,
			util.RuntimeProtocolVersion,
			util.RuntimeProtocolVersion,
			migrationState,
			installationID,
		)
		if err != nil {
			return err
		}
	} else {
		const insertInstallationSQL = `
		INSERT INTO installation_metadata (
			installation_id,
			database_format_version,
			schema_compatibility_major,
			minimum_runtime_version,
			last_opened_runtime_version,
			maintenance_state
		) VALUES (?, ?, ?, ?, ?, ?);
		`
		_, err := db.Exec(
			insertInstallationSQL,
			ulid.Make().String(),
			DBFormatVersion,
			schema.CompatibilityMajor,
			util.RuntimeProtocolVersion,
			util.RuntimeProtocolVersion,
			migrationState,
		)

		return err
	}
	return nil
}
