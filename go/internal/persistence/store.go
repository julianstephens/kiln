package persistence

import (
	"context"
	"database/sql"
	"os"
	"path/filepath"
	"time"

	_ "github.com/mattn/go-sqlite3"
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
}

type StoreKind string

const (
	TursoStoreKind  StoreKind = "turso"
	SqliteStoreKind StoreKind = "sqlite3"
)

// Open opens a new Store based on the provided kind and path.
func Open(cfg Config) (Store, error) {
	validatedPath, err := validateStorePath(cfg.InstallationDBPath)
	if err != nil {
		return nil, err
	}

	conn, err := sql.Open(string(cfg.DBType), *validatedPath)
	if err != nil {
		return nil, NewStoreOpenFailedError(*validatedPath, err)
	}

	conn.SetMaxOpenConns(cfg.MaxOpenConnections)
	conn.SetMaxIdleConns(cfg.MaxIdleConnections)
	conn.SetConnMaxLifetime(time.Duration(cfg.MaxConnectionLifetimeSeconds) * time.Second)

	switch cfg.DBType {
	case TursoStoreKind:
		return &TursoStore{
			Path: cfg.InstallationDBPath,
			Conn: conn,
		}, nil
	case SqliteStoreKind:
		return &SqliteStore{
			Path: cfg.InstallationDBPath,
			Conn: conn,
		}, nil
	default:
		return nil, NewStoreNotFoundError(cfg.InstallationDBPath)
	}
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

func validateStorePath(path string) (validated *string, err error) {
	if len(path) == 0 {
		return nil, NewStoreError(path, CodeInvalidPath, "store path must be provided", nil)
	}
	cleaned := filepath.Clean(path)
	if cleaned == ":memory:" {
		return &cleaned, nil
	}
	if !isDBFileAndExists(cleaned) {
		return nil, NewStoreError(path, CodeInvalidPath, "provided store path must be an existing .db file", nil)
	}
	return
}

func isDBFileAndExists(path string) bool {
	info, err := os.Stat(path)
	if err != nil {
		return false
	}
	if info.IsDir() {
		return false
	}
	return info.Mode().IsRegular() && filepath.Ext(path) == ".db"
}
