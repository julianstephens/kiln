package persistence

import (
	"fmt"

	runtime_error "github.com/julianstephens/kiln/go/schema/runtime/error"
)

type Error struct {
	Code      string                               `json:"code"`
	Category  runtime_error.ErrorKilnErrorCategory `json:"category"`
	StorePath string                               `json:"store_path"`
	Message   string                               `json:"message"`
	Retryable bool                                 `json:"retryable"`
	Cause     error                                `json:"cause,omitempty"`
}

func (e *Error) Error() string {
	if e.Cause != nil {
		return fmt.Sprintf("%s: %s (cause: %v)", e.Code, e.Message, e.Cause)
	}
	return fmt.Sprintf("%s: %s", e.Code, e.Message)
}

func (e *Error) Details() map[string]any {
	return map[string]any{
		"store_path": e.StorePath,
		"cause":      e.Cause,
	}
}

const (
	CodeStoreNotFound             = "store_not_found"
	CodeStoreClosed               = "store_closed"
	CodeStoreNotOpen              = "store_not_open"
	CodeHealthCheckFailed         = "health_check_failed"
	CodeStoreOpenFailed           = "store_open_failed"
	CodeStoreCloseFailed          = "store_close_failed"
	CodeInvalidPath               = "invalid_store_path"
	CodeStoreInitializationFailed = "store_initialization_failed"
)

var (
	NewStoreNotFoundError = func(storePath string) *Error {
		return &Error{
			Code:      CodeStoreNotFound,
			Category:  runtime_error.ErrorKilnErrorCategoryValidation,
			StorePath: storePath,
			Retryable: false,
			Message:   fmt.Sprintf("store not found at path: %s", storePath),
		}
	}
	NewStoreClosedError = func(storePath string) *Error {
		return &Error{
			Code:      CodeStoreClosed,
			Category:  runtime_error.ErrorKilnErrorCategoryInternal,
			StorePath: storePath,
			Retryable: false,
			Message:   "store is closed",
		}
	}
	NewStoreNotOpenError = func(storePath string) *Error {
		return &Error{
			Code:      CodeStoreNotOpen,
			Category:  runtime_error.ErrorKilnErrorCategoryInternal,
			StorePath: storePath,
			Retryable: false,
			Message:   "store is not open",
		}
	}
	NewHealthCheckFailedError = func(storePath string, cause error) *Error {
		return &Error{
			Code:      CodeHealthCheckFailed,
			Category:  runtime_error.ErrorKilnErrorCategoryInternal,
			StorePath: storePath,
			Retryable: true,
			Message:   "health check failed",
			Cause:     cause,
		}
	}
	NewStoreOpenFailedError = func(storePath string, cause error) *Error {
		return &Error{
			Code:      CodeStoreOpenFailed,
			Category:  runtime_error.ErrorKilnErrorCategoryInternal,
			StorePath: storePath,
			Retryable: false,
			Message:   fmt.Sprintf("failed to open store at path: %s", storePath),
			Cause:     cause,
		}
	}
	NewStoreCloseFailedError = func(storePath string, cause error) *Error {
		return &Error{
			Code:      CodeStoreCloseFailed,
			Category:  runtime_error.ErrorKilnErrorCategoryInternal,
			StorePath: storePath,
			Retryable: false,
			Message:   fmt.Sprintf("failed to close store at path: %s", storePath),
			Cause:     cause,
		}
	}
	NewStoreError = func(storePath string, code string, category runtime_error.ErrorKilnErrorCategory, message string, retryable bool, cause error) *Error {
		return &Error{
			Code:      code,
			Category:  category,
			StorePath: storePath,
			Message:   message,
			Retryable: retryable,
			Cause:     cause,
		}
	}
)

const (
	CodeMigrationLockFailed      = "migration_lock_failed"
	CodeUnsupportedSchemaVersion = "unsupported_schema_version"
	CodeMigrationFailed          = "migration_failed"
)

var (
	NewMigrationLockFailedError = func(storePath string, cause error) *Error {
		return &Error{
			Code:      CodeMigrationLockFailed,
			Category:  runtime_error.ErrorKilnErrorCategoryInternal,
			StorePath: storePath,
			Message:   "failed to acquire migration lock",
			Cause:     cause,
		}
	}
	NewMigrationFailedError = func(storePath string, cause error) *Error {
		return &Error{
			Code:      CodeMigrationFailed,
			Category:  runtime_error.ErrorKilnErrorCategoryInternal,
			StorePath: storePath,
			Message:   "migration failed",
			Cause:     cause,
		}
	}
	NewSchemaVersionMismatchError = func(storePath string, got int64, expected int64) *Error {
		return &Error{
			Code:      CodeUnsupportedSchemaVersion,
			Category:  runtime_error.ErrorKilnErrorCategoryCompatibility,
			StorePath: storePath,
			Message:   "database schema version is not compatible with the application",
			Cause:     fmt.Errorf("got version %d, expected %d", got, expected),
		}
	}
	NewCompatibilityMajorMismatchError = func(storePath string, got int, expected int) *Error {
		return &Error{
			Code:      CodeUnsupportedSchemaVersion,
			Category:  runtime_error.ErrorKilnErrorCategoryCompatibility,
			StorePath: storePath,
			Message:   "database schema compatibility major is not compatible with the application",
			Cause:     fmt.Errorf("got compatibility major %d, expected %d", got, expected),
		}
	}
)
