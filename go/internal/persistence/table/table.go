package table

import (
	"context"
	"database/sql"
	"errors"
)

const (
	DefaultQueryTimeout = 5 // in seconds
)

var ErrExecutorNotInitialized = errors.New("executor not initialized: either tx or db must be set")

type Table interface {
	// SetExecutor sets the executor for the table, which can be either a transaction or a database connection.
	SetExecutor(*Executor)
	// TableName returns the name of the table associated with the struct.
	TableName() string
	// Exists checks if the table exists in the database. Returns true if it exists, false otherwise.
	Exists(context.Context) (bool, error)
}

type Row interface {
	// SetExecutor sets the executor for the row, which can be either a transaction or a database connection.
	SetExecutor(*Executor)
	// TableName returns the name of the table associated with the struct.
	TableName() string
	// Laod retrieves the record from the table into the struct based on its primary key. Returns true if a record was found, false otherwise.
	Load(context.Context) (bool, error)
	// LoadFirst retrieves the first record from the table into the struct. Returns true if a record was found, false otherwise.
	LoadFirst(context.Context) (bool, error)
	// Insert inserts the struct into the table. Returns an error if the insert fails.
	Insert(context.Context) error
	// Update updates the record in the table. Returns the number of rows affected and an error if the update fails.
	Update(context.Context) (int64, error)
	// Delete deletes the record from the table. Returns the number of rows affected and an error if the delete fails.
	Delete(context.Context) (int64, error)
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

type Executor struct {
	tx *sql.Tx
	db *sql.DB
}

// NewExecutorWithTx creates a new Executor with a transaction.
func NewExecutorWithTx(tx *sql.Tx) *Executor {
	return &Executor{tx: tx}
}

// NewExecutorWithDB creates a new Executor with a database connection.
func NewExecutorWithDB(db *sql.DB) *Executor {
	return &Executor{db: db}
}

// ExecContext executes a query that doesn't return rows, such as an INSERT, UPDATE, or DELETE.
// It returns the result of the execution and any error encountered.
func (e *Executor) ExecContext(ctx context.Context, query string, args []any) (sql.Result, error) {
	if e.tx == nil && e.db == nil {
		return nil, ErrExecutorNotInitialized
	}

	if e.tx != nil {
		return e.tx.ExecContext(ctx, query, args...)
	}

	return e.db.ExecContext(ctx, query, args...)
}

// QueryRowContext executes a query that is expected to return at most one row. It returns the row and any error encountered.
// If no rows are returned, the returned *sql.Row will return ErrNoRows when Scan is called.
func (e *Executor) QueryRowContext(ctx context.Context, query string, args []any) (*sql.Row, error) {
	if e.tx == nil && e.db == nil {
		return nil, ErrExecutorNotInitialized
	}

	if e.tx != nil {
		return e.tx.QueryRowContext(ctx, query, args...), nil
	}

	return e.db.QueryRowContext(ctx, query, args...), nil
}

// QueryContext executes a query that returns rows, typically a SELECT. It returns the resulting rows and any error encountered.
func (e *Executor) QueryContext(ctx context.Context, query string, args []any) (*sql.Rows, error) {
	if e.tx == nil && e.db == nil {
		return nil, ErrExecutorNotInitialized
	}

	if e.tx != nil {
		return e.tx.QueryContext(ctx, query, args...)
	}

	return e.db.QueryContext(ctx, query, args...)
}
