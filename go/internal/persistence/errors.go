package persistence

import "fmt"

type Error struct {
	Code      string `json:"code"`
	StorePath string `json:"store_path"`
	Message   string `json:"message"`
	Cause     error  `json:"cause,omitempty"`
}

func (e *Error) Error() string {
	if e.Cause != nil {
		return fmt.Sprintf("%s: %s (cause: %v)", e.Code, e.Message, e.Cause)
	}
	return fmt.Sprintf("%s: %s", e.Code, e.Message)
}

const (
	CodeStoreNotFound     = "store_not_found"
	CodeStoreClosed       = "store_closed"
	CodeStoreNotOpen      = "store_not_open"
	CodeHealthCheckFailed = "health_check_failed"
	CodeStoreOpenFailed   = "store_open_failed"
	CodeStoreCloseFailed  = "store_close_failed"
	CodeInvalidPath       = "invalid_store_path"
)

var (
	NewStoreNotFoundError = func(storePath string) *Error {
		return &Error{
			Code:      CodeStoreNotFound,
			StorePath: storePath,
			Message:   fmt.Sprintf("store not found at path: %s", storePath),
		}
	}
	NewStoreClosedError = func(storePath string) *Error {
		return &Error{
			Code:      CodeStoreClosed,
			StorePath: storePath,
			Message:   "store is closed",
		}
	}
	NewStoreNotOpenError = func(storePath string) *Error {
		return &Error{
			Code:      CodeStoreNotOpen,
			StorePath: storePath,
			Message:   "store is not open",
		}
	}
	NewHealthCheckFailedError = func(storePath string, cause error) *Error {
		return &Error{
			Code:      CodeHealthCheckFailed,
			StorePath: storePath,
			Message:   "health check failed",
			Cause:     cause,
		}
	}
	NewStoreOpenFailedError = func(storePath string, cause error) *Error {
		return &Error{
			Code:      CodeStoreOpenFailed,
			StorePath: storePath,
			Message:   fmt.Sprintf("failed to open store at path: %s", storePath),
			Cause:     cause,
		}
	}
	NewStoreCloseFailedError = func(storePath string, cause error) *Error {
		return &Error{
			Code:      CodeStoreCloseFailed,
			StorePath: storePath,
			Message:   fmt.Sprintf("failed to close store at path: %s", storePath),
			Cause:     cause,
		}
	}
	NewStoreError = func(storePath string, code string, message string, cause error) *Error {
		return &Error{
			Code:      code,
			StorePath: storePath,
			Message:   message,
			Cause:     cause,
		}
	}
)

const (
	CodeMigrationLockFailed   = "migration_lock_failed"
	CodeSchemaVersionMismatch = "schema_version_mismatch"
	CodeMigrationFailed       = "migration_failed"
)

var (
	NewMigrationLockFailedError = func(storePath string, cause error) *Error {
		return &Error{
			Code:      CodeMigrationLockFailed,
			StorePath: storePath,
			Message:   "failed to acquire migration lock",
			Cause:     cause,
		}
	}
	NewMigrationFailedError = func(storePath string, cause error) *Error {
		return &Error{
			Code:      CodeMigrationFailed,
			StorePath: storePath,
			Message:   "migration failed",
			Cause:     cause,
		}
	}
	NewSchemaVersionMismatchError = func(storePath string, got int, expected int) *Error {
		return &Error{
			Code:      CodeSchemaVersionMismatch,
			StorePath: storePath,
			Message:   "schema compatibility major newer than expected",
			Cause:     fmt.Errorf("got compatibility major %d, expected %d", got, expected),
		}
	}
)
