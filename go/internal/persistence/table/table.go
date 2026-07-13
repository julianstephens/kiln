package table

import (
	"context"
	"database/sql"
)

const (
	DefaultQueryTimeout = 5 // in seconds
)

type Table interface {
	// TableName returns the name of the table associated with the struct.
	TableName() string
	// Exists checks if the table exists in the database. Returns true if it exists, false otherwise.
	Exists(ctx context.Context, db *sql.DB) (bool, error)
}

type Row interface {
	// TableName returns the name of the table associated with the struct.
	TableName() string
	// Laod retrieves the record from the table into the struct based on its primary key. Returns true if a record was found, false otherwise.
	Load(ctx context.Context, db *sql.DB) (bool, error)
	// LoadFirst retrieves the first record from the table into the struct. Returns true if a record was found, false otherwise.
	LoadFirst(ctx context.Context, db *sql.DB) (bool, error)
	// Insert inserts the struct into the table. Returns an error if the insert fails.
	Insert(ctx context.Context, db *sql.DB) error
	// Update updates the record in the table. Returns the number of rows affected and an error if the update fails.
	Update(ctx context.Context, db *sql.DB) (int64, error)
	// Delete deletes the record from the table. Returns the number of rows affected and an error if the delete fails.
	Delete(ctx context.Context, db *sql.DB) (int64, error)
}

// IsSet checks if a pointer to a value is set (non-nil and non-zero if it implements IsZero).
func IsSet[T any](value *T) bool {
	if value == nil {
		return false
	}

	if v, ok := any(*value).(interface{ IsZero() bool }); ok {
		return !v.IsZero()
	}

	return true
}
