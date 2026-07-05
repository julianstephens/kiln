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

// MustObject creates a new protocol.ErrorObject based on the provided Spec.
func MustObject(spec Spec) (protocol.ErrorObject, runtime_error.ErrorKilnError) {
	kilnErr := runtime_error.Error{
		KilnError: runtime_error.ErrorKilnError{
			Code:      spec.KilnCode,
			Category:  spec.Category,
			Message:   spec.Message,
			Retryable: spec.Retryable,
			Details:   normalizeDetails(spec.Details),
		},
	}
	if err := kilnErr.Validate(); err != nil {
		panic("failed to validate error data for method " + spec.Method + ": " + err.Error())
	}
	return protocol.ErrorObject{
		Code:    spec.JSONRPCCode,
		Message: spec.Message,
		Data:    util.MustStructToMap(kilnErr),
	}, kilnErr.KilnError
}

// Response creates a new protocol.ErrorResponse based on the provided Spec and ID.
func Response(id protocol.ID, spec Spec) (protocol.ErrorResponse, runtime_error.ErrorKilnError) {
	obj, kilnErr := MustObject(spec)
	return protocol.ErrorResponse{
		JSONRPC: protocol.DefaultJSONRPCVersion,
		ID:      id,
		Error:   obj,
	}, kilnErr
}

// MethodNotFound creates a new protocol.ErrorResponse for a method not found error.
func MethodNotFound(id protocol.ID, method string) (protocol.ErrorResponse, runtime_error.ErrorKilnError) {
	spec := Spec{
		Method:      method,
		JSONRPCCode: contract.JSONRPCMethodNotFound,
		Category:    runtime_error.ErrorKilnErrorCategoryCompatibility,
		KilnCode:    "runtime.method_not_found",
		Message:     "method not found",
		Retryable:   false,
		Details: map[string]any{
			"requested_method":            method,
			"supported_methods":           protocol.SupportedMethods(),
			"supported_method_namespaces": protocol.SupportedMethodNamespaces(),
		},
	}
	return Response(id, spec)
}

// InvalidParams creates a new protocol.ErrorResponse for an invalid params error.
func InvalidParams(
	id protocol.ID,
	method string,
	details map[string]any,
) (protocol.ErrorResponse, runtime_error.ErrorKilnError) {
	spec := Spec{
		Method:      method,
		JSONRPCCode: contract.JSONRPCInvalidParams,
		Category:    runtime_error.ErrorKilnErrorCategoryValidation,
		KilnCode:    "runtime.invalid_params",
		Message:     "invalid params for method: " + method,
		Retryable:   false,
		Details:     normalizeDetails(details),
	}
	return Response(id, spec)
}

// Internal creates a new protocol.ErrorResponse for an internal error.
func Internal(
	id protocol.ID,
	method *string,
	message string,
	details map[string]any,
) (protocol.ErrorResponse, runtime_error.ErrorKilnError) {
	var specMethod string
	if method == nil {
		specMethod = "unknown"
	} else {
		specMethod = *method
	}
	spec := Spec{
		Method:      specMethod,
		JSONRPCCode: contract.JSONRPCInternalError,
		Category:    runtime_error.ErrorKilnErrorCategoryInternal,
		KilnCode:    "runtime.internal_error",
		Message:     message,
		Retryable:   false,
		Details:     normalizeDetails(details),
	}
	return Response(id, spec)
}

// ParseError creates a new protocol.ErrorResponse for a parse error.
func ParseError(details map[string]any) (protocol.ErrorResponse, runtime_error.ErrorKilnError) {
	spec := Spec{
		Method:      "unknown",
		JSONRPCCode: contract.JSONRPCParseError,
		Category:    runtime_error.ErrorKilnErrorCategoryValidation,
		KilnCode:    "runtime.parse_error",
		Message:     "unable to parse JSON-RPC request",
		Retryable:   false,
		Details:     normalizeDetails(details),
	}
	return Response(protocol.ID{Null: true}, spec)
}

// InvalidRequest creates a new protocol.ErrorResponse for an invalid request error.
func InvalidRequest(
	id protocol.ID,
	method string,
	details map[string]any,
) (protocol.ErrorResponse, runtime_error.ErrorKilnError) {
	spec := Spec{
		Method:      method,
		JSONRPCCode: contract.JSONRPCInvalidRequest,
		Category:    runtime_error.ErrorKilnErrorCategoryValidation,
		KilnCode:    "runtime.invalid_request",
		Message:     "invalid request for method: " + method,
		Retryable:   false,
		Details:     normalizeDetails(details),
	}
	return Response(id, spec)
}

// Draining creates a new protocol.ErrorResponse for a server draining error.
func Draining(id protocol.ID, method string) (protocol.ErrorResponse, runtime_error.ErrorKilnError) {
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
	return Response(id, spec)
}

// Shutdown creates a new protocol.ErrorResponse for a server shutdown error.
func Shutdown(id protocol.ID, method string) (protocol.ErrorResponse, runtime_error.ErrorKilnError) {
	spec := Spec{
		Method:      method,
		JSONRPCCode: contract.JSONRPCInvalidRequest,
		Category:    runtime_error.ErrorKilnErrorCategoryShutdown,
		KilnCode:    "runtime.server_shutting_down",
		Message:     "server is shutting down and cannot accept new requests",
		Retryable:   false,
		Details: map[string]any{
			"received_method": method,
		},
	}
	return Response(id, spec)
}

func normalizeDetails(details map[string]any) map[string]any {
	if details == nil {
		return map[string]any{}
	}
	return details
}
