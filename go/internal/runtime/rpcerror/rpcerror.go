package rpcerror

import (
	"github.com/julianstephens/kiln/go/internal/protocol"
	"github.com/julianstephens/kiln/go/internal/runtime/contract"
	"github.com/julianstephens/kiln/go/internal/util"
	runtime_error "github.com/julianstephens/kiln/go/schema/runtime/error"
)

// Spec defines the specification for creating a new error object and kiln error.
type Spec struct {
	JSONRPCCode int
	KilnCode    string
	Method      string
	Category    runtime_error.ErrorKilnErrorCategory
	Message     string
	Retryable   bool
	Details     map[string]any
}

// NewObject creates a new protocol.ErrorObject and runtime_error.ErrorKilnError based on the provided Spec.
func NewObject(spec Spec) (protocol.ErrorObject, runtime_error.ErrorKilnError) {
	return MustObject(spec), runtime_error.ErrorKilnError{
		Code:      spec.KilnCode,
		Category:  spec.Category,
		Message:   spec.Message,
		Retryable: spec.Retryable,
		Details:   util.If(spec.Details == nil, make(map[string]any), spec.Details),
	}
}

// MustObject creates a new protocol.ErrorObject based on the provided Spec.
func MustObject(spec Spec) protocol.ErrorObject {
	kilnErr := runtime_error.Error{
		KilnError: runtime_error.ErrorKilnError{
			Code:      spec.KilnCode,
			Category:  spec.Category,
			Message:   spec.Message,
			Retryable: spec.Retryable,
			Details:   util.If(spec.Details == nil, make(map[string]any), spec.Details),
		},
	}
	errMap := util.MustStructToMap(kilnErr)
	methodSpec, ok := protocol.KilnMethods[spec.Method]
	if !ok {
		return protocol.ErrorObject{
			Code:    spec.JSONRPCCode,
			Message: spec.Message,
			Data:    errMap,
		}
	}
	validated, err := methodSpec.ValidateErrorData(errMap)
	if err != nil {
		panic("failed to validate error data for method " + spec.Method + ": " + err.Error())
	}
	return protocol.ErrorObject{
		Code:    spec.JSONRPCCode,
		Message: spec.Message,
		Data:    util.MustStructToMap(validated),
	}
}

// Response creates a new protocol.ErrorResponse based on the provided Spec and ID.
func Response(id protocol.ID, spec Spec) protocol.ErrorResponse {
	return protocol.ErrorResponse{
		JSONRPC: protocol.DefaultJSONRPCVersion,
		ID:      id,
		Error:   MustObject(spec),
	}
}

// MethodNotFound creates a new protocol.ErrorResponse for a method not found error.
func MethodNotFound(id protocol.ID, method string) protocol.ErrorResponse {
	spec := Spec{
		Method:      method,
		JSONRPCCode: contract.JSONRPCMethodNotFound,
		Category:    runtime_error.ErrorKilnErrorCategoryValidation,
		KilnCode:    "runtime.method_not_found",
		Message:     "method_not_found: " + method,
		Retryable:   false,
		Details: map[string]any{
			"received_method":             method,
			"supported_methods":           protocol.SupportedMethods(),
			"supported_method_namespaces": protocol.SupportedMethodNamespaces(),
		},
	}
	return protocol.ErrorResponse{
		JSONRPC: protocol.DefaultJSONRPCVersion,
		ID:      id,
		Error:   MustObject(spec),
	}
}

// InvalidParams creates a new protocol.ErrorResponse for an invalid params error.
func InvalidParams(id protocol.ID, method string, details map[string]any) protocol.ErrorResponse {
	spec := Spec{
		Method:      method,
		JSONRPCCode: contract.JSONRPCInvalidParams,
		Category:    runtime_error.ErrorKilnErrorCategoryValidation,
		KilnCode:    "runtime.invalid_params",
		Message:     "invalid params for method: " + method,
		Retryable:   false,
		Details:     util.If(details == nil, make(map[string]any), details),
	}
	return protocol.ErrorResponse{
		JSONRPC: protocol.DefaultJSONRPCVersion,
		ID:      id,
		Error:   MustObject(spec),
	}
}

// Internal creates a new protocol.ErrorResponse for an internal error.
func Internal(id protocol.ID, method *string, message string, details map[string]any) protocol.ErrorResponse {
	spec := Spec{
		Method:      util.If(method == nil, "unknown", *method),
		JSONRPCCode: contract.JSONRPCInternalError,
		Category:    runtime_error.ErrorKilnErrorCategoryInternal,
		KilnCode:    "runtime.internal_error",
		Message:     message,
		Retryable:   false,
		Details:     util.If(details == nil, make(map[string]any), details),
	}
	return protocol.ErrorResponse{
		JSONRPC: protocol.DefaultJSONRPCVersion,
		ID:      id,
		Error:   MustObject(spec),
	}
}

// ParseError creates a new protocol.ErrorResponse for a parse error.
func ParseError(details map[string]any) protocol.ErrorResponse {
	spec := Spec{
		Method:      "unknown",
		JSONRPCCode: contract.JSONRPCParseError,
		Category:    runtime_error.ErrorKilnErrorCategoryValidation,
		KilnCode:    "runtime.parse_error",
		Message:     "parse error",
		Retryable:   false,
		Details:     util.If(details == nil, make(map[string]any), details),
	}
	return protocol.ErrorResponse{
		JSONRPC: protocol.DefaultJSONRPCVersion,
		Error:   MustObject(spec),
	}
}

// InvalidRequest creates a new protocol.ErrorResponse for an invalid request error.
func InvalidRequest(id protocol.ID, method string, details map[string]any) protocol.ErrorResponse {
	spec := Spec{
		Method:      method,
		JSONRPCCode: contract.JSONRPCInvalidRequest,
		Category:    runtime_error.ErrorKilnErrorCategoryValidation,
		KilnCode:    "runtime.invalid_request",
		Message:     "invalid request for method: " + method,
		Retryable:   false,
		Details:     util.If(details == nil, make(map[string]any), details),
	}
	return protocol.ErrorResponse{
		JSONRPC: protocol.DefaultJSONRPCVersion,
		ID:      id,
		Error:   MustObject(spec),
	}
}

// Draining creates a new protocol.ErrorResponse for a server draining error.
func Draining(id protocol.ID, method string) protocol.ErrorResponse {
	spec := Spec{
		Method:      method,
		JSONRPCCode: contract.JSONRPCInvalidRequest,
		Category:    runtime_error.ErrorKilnErrorCategoryLifecycle,
		KilnCode:    "runtime.server_draining",
		Message:     "server is draining and cannot accept new requests",
		Retryable:   false,
		Details: map[string]any{
			"received_method": method,
		},
	}
	return protocol.ErrorResponse{
		JSONRPC: protocol.DefaultJSONRPCVersion,
		ID:      id,
		Error:   MustObject(spec),
	}
}

// Shutdown creates a new protocol.ErrorResponse for a server shutdown error.
func Shutdown(id protocol.ID, method string) protocol.ErrorResponse {
	spec := Spec{
		Method:      method,
		JSONRPCCode: contract.JSONRPCInvalidRequest,
		Category:    runtime_error.ErrorKilnErrorCategoryShutdown,
		KilnCode:    "runtime.server_shutting_down",
		Message:     "server is shutting down and cannot accept new requests",
		Details: map[string]any{
			"received_method": method,
		},
	}
	return protocol.ErrorResponse{
		JSONRPC: protocol.DefaultJSONRPCVersion,
		ID:      id,
		Error:   MustObject(spec),
	}
}
