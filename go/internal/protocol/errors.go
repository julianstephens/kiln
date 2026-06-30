package protocol

import "fmt"

type Error struct {
	Code      string         `json:"code"`
	Message   string         `json:"message"`
	Retryable bool           `json:"retryable"`
	Details   map[string]any `json:"details,omitempty"`
}

func (e *Error) Error() string {
	return fmt.Sprintf("%s: %s", e.Code, e.Message)
}

var (
	CodeFrameTooLarge = "frame_too_large"
	CodeInvalidFrame  = "invalid_frame"
	CodeFramingError  = "invalid_json"

	NewFrameTooLargeError = func(frameLength, maxBytes int) *Error {
		return &Error{
			Code:      CodeFrameTooLarge,
			Message:   fmt.Sprintf("frame length %d exceeds maximum size of %d bytes", frameLength, maxBytes),
			Retryable: false,
		}
	}
	ErrEmbeddedNewline = &Error{
		Code:      CodeInvalidFrame,
		Message:   "frame contains newline character",
		Retryable: false,
	}
	NewFramingError = func(err error) *Error {
		return &Error{
			Code:      CodeFramingError,
			Message:   fmt.Sprintf("invalid JSON: %v", err),
			Retryable: false,
		}
	}
)

var (
	CodeInvalidJSONRPCVersion     = "invalid_jsonrpc_version"
	CodeInvalidJSONRPCRequest     = "invalid_jsonrpc_request"
	CodeInvalidJSONRPCFrame       = "invalid_jsonrpc_frame"
	CodeInvalidID                 = "invalid_id"
	NewInvalidJSONRPCRequestError = func(message string, retryable bool, details map[string]any) *Error {
		return &Error{
			Code:      CodeInvalidJSONRPCRequest,
			Message:   message,
			Retryable: retryable,
			Details:   details,
		}
	}
	NewInvalidJSONRPCFrameError = func(message string) *Error {
		return &Error{
			Code:      CodeInvalidJSONRPCFrame,
			Message:   message,
			Retryable: false,
		}
	}
	ErrInvalidJSONRPCVersion = &Error{
		Code:      CodeInvalidJSONRPCVersion,
		Message:   "invalid JSON-RPC version",
		Retryable: false,
	}
	NewInvalidIDError = func(message string, retryable bool, details map[string]any) *Error {
		return &Error{
			Code:      CodeInvalidID,
			Message:   message,
			Retryable: retryable,
			Details:   details,
		}
	}
)

var (
	CodeRuntimeStreamClosed     = "runtime_stream_closed"
	CodeReadStreamError         = "read_stream_error"
	NewRuntimeStreamClosedError = func(message string, retryable bool, details map[string]any) *Error {
		return &Error{
			Code:      CodeRuntimeStreamClosed,
			Message:   message,
			Retryable: retryable,
			Details:   details,
		}
	}
	NewReadStreamError = func(message string, retryable bool, details map[string]any) *Error {
		return &Error{
			Code:      CodeReadStreamError,
			Message:   message,
			Retryable: retryable,
			Details:   details,
		}
	}
)
