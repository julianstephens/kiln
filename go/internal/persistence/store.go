package persistence

import (
	"context"
	"database/sql"
	"os"
	"path/filepath"
	"time"
)

type Store interface {
	Close() error
	Health(ctx context.Context) error
}

type StoreKind string

const (
	TursoStoreKind  StoreKind = "turso"
	SqliteStoreKind StoreKind = "sqlite"
)

// Open opens a new Store based on the provided kind and path.
func Open(kind StoreKind, path string) (Store, error) {
	validatedPath, err := validateStorePath(path)
	if err != nil {
		return nil, err
	}

	conn, err := sql.Open(string(kind), *validatedPath)
	if err != nil {
		return nil, NewStoreOpenFailedError(*validatedPath, err)
	}

	switch kind {
	case TursoStoreKind:
		return &TursoStore{
			Path: path,
			Conn: conn,
		}, nil
	case SqliteStoreKind:
		return &SqliteStore{
			Path: path,
			Conn: conn,
		}, nil
	default:
		return nil, NewStoreNotFoundError(path)
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
	if !info.IsDir() {
		return false
	}
	return info.Mode().IsRegular() && filepath.Ext(path) == ".db"
}
