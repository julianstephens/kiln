package persistence

import (
	"context"
	"database/sql"
	"errors"
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

	exists := false
	if *validatedPath != ":memory:" {
		exists, err = ensurePath(installationDir, true)
		if err != nil {
			return nil, NewStoreError(
				*validatedPath,
				CodeInvalidPath,
				"failed to ensure installation directory exists",
				err,
			)
		}
	}

	conn, err := sql.Open(string(cfg.DBType), *validatedPath)
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
		compatibilityMajor, err := getCompatibilityMajor(store.GetDB())
		if err != nil {
			if !errors.Is(err, sql.ErrNoRows) {
				return nil, NewMigrationFailedError(cfg.InstallationDBPath, err)
			}
		}
		if compatibilityMajor > schema.CompatibilityMajor {
			return nil, NewSchemaVersionMismatchError(
				cfg.InstallationDBPath,
				compatibilityMajor,
				schema.CompatibilityMajor,
			)
		}
	}

	migrationErr := migrate(store.GetDB())
	if migrationErr != nil {
		return nil, NewMigrationFailedError(cfg.InstallationDBPath, migrationErr)
	}

	if err := initializeDatabase(store.GetDB()); err != nil {
		return nil, NewStoreError(cfg.InstallationDBPath, CodeInvalidPath, "failed to initialize database", err)
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

func getCompatibilityMajor(db *sql.DB) (int, error) {
	var version int
	row := db.QueryRow("SELECT schema_compatibility_major FROM installation_metadata;")
	if err := row.Scan(&version); err != nil {
		return 0, err
	}
	return version, nil
}

func initializeDatabase(db *sql.DB) error {
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
		"normal",
	)
	return err
}
