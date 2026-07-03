package runtime

import (
	"github.com/julianstephens/kiln/go/internal/protocol"
	"github.com/julianstephens/kiln/go/internal/runtime/contract"
	runtime_error "github.com/julianstephens/kiln/go/schema/runtime/error"
)

type Error struct {
	Code    string `json:"code"`
	Message string `json:"message"`
	Details string `json:"details,omitempty"`
}

func (e *Error) Error() string {
	if e.Details != "" {
		return e.Code + ": " + e.Message + " (" + e.Details + ")"
	}
	return e.Code + ": " + e.Message
}

const (
	CodeInputStreamMissing  = "input_stream_missing"
	CodeOutputStreamMissing = "output_stream_missing"
	CodeLogSinkOpenFailed   = "log_sink_open_failed"
)

var (
	ErrInputStreamMissing = &Error{
		Code:    CodeInputStreamMissing,
		Message: "input stream is missing",
	}
	ErrOutputStreamMissing = &Error{
		Code:    CodeOutputStreamMissing,
		Message: "output stream is missing",
	}
)

const (
	CodeInvalidJSONRPCFrame = "invalid_jsonrpc_frame"
)

var NewInvalidJSONRPCFrameError = func(details string) *Error {
	return &Error{
		Code:    CodeInvalidJSONRPCFrame,
		Message: "invalid JSON-RPC frame",
		Details: details,
	}
}

var NewInvalidRequestError = func(message string, data runtime_error.Error) *protocol.ErrorObject {
	return &protocol.ErrorObject{
		Code:    contract.JSONRPCInvalidRequest,
		Message: message,
		Data:    data,
	}
}
