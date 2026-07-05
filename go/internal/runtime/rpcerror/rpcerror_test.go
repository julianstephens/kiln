package rpcerror_test

import (
	"encoding/json"
	"reflect"
	"testing"

	utest "github.com/julianstephens/go-utils/tests"

	"github.com/julianstephens/kiln/go/internal/protocol"
	"github.com/julianstephens/kiln/go/internal/runtime/contract"
	"github.com/julianstephens/kiln/go/internal/runtime/rpcerror"
	runtime_error "github.com/julianstephens/kiln/go/schema/runtime/error"
)

func validateRuntimeErrorData(t *testing.T, data map[string]any) {
	t.Helper()

	raw, err := json.Marshal(data)
	utest.RequireNoError(t, err)

	var validated runtime_error.Error
	utest.RequireNoError(t, json.Unmarshal(raw, &validated))
	utest.RequireNoError(t, validated.Validate())
}

func TestNamedConstructorsProduceSchemaValidErrorData(t *testing.T) {
	t.Parallel()

	method := "runtime.initialize"
	methodPtr := &method

	tests := []struct {
		name     string
		spec     rpcerror.Spec
		response func() protocol.ErrorResponse
	}{
		{
			name: "method not found",
			spec: rpcerror.Spec{
				JSONRPCCode: contract.JSONRPCMethodNotFound,
				KilnCode:    "runtime.method_not_found",
				Method:      "runtime.unknown",
				Category:    runtime_error.ErrorKilnErrorCategoryCompatibility,
				Message:     "method_not_found: runtime.unknown",
				Retryable:   false,
				Details: map[string]any{
					"received_method":             "runtime.unknown",
					"supported_methods":           protocol.SupportedMethods(),
					"supported_method_namespaces": protocol.SupportedMethodNamespaces(),
				},
			},
			response: func() protocol.ErrorResponse {
				err, _ := rpcerror.MethodNotFound(protocol.ID{}, "runtime.unknown")
				return err
			},
		},
		{
			name: "invalid params",
			spec: rpcerror.Spec{
				JSONRPCCode: contract.JSONRPCInvalidParams,
				KilnCode:    "runtime.invalid_params",
				Method:      method,
				Category:    runtime_error.ErrorKilnErrorCategoryValidation,
				Message:     "invalid params for method: " + method,
				Retryable:   false,
				Details: map[string]any{
					"missing": "query",
				},
			},
			response: func() protocol.ErrorResponse {
				err, _ := rpcerror.InvalidParams(protocol.ID{}, method, map[string]any{
					"missing": "query",
				})
				return err
			},
		},
		{
			name: "internal",
			spec: rpcerror.Spec{
				JSONRPCCode: contract.JSONRPCInternalError,
				KilnCode:    "runtime.internal_error",
				Method:      method,
				Category:    runtime_error.ErrorKilnErrorCategoryInternal,
				Message:     "runtime exploded",
				Retryable:   false,
				Details: map[string]any{
					"reason": "unexpected",
				},
			},
			response: func() protocol.ErrorResponse {
				err, _ := rpcerror.Internal(protocol.ID{}, methodPtr, "runtime exploded", map[string]any{
					"reason": "unexpected",
				})
				return err
			},
		},
		{
			name: "parse error",
			spec: rpcerror.Spec{
				JSONRPCCode: contract.JSONRPCParseError,
				KilnCode:    "runtime.parse_error",
				Method:      "unknown",
				Category:    runtime_error.ErrorKilnErrorCategoryValidation,
				Message:     "unable to parse JSON-RPC request",
				Retryable:   false,
				Details: map[string]any{
					"offset": 12,
				},
			},
			response: func() protocol.ErrorResponse {
				err, _ := rpcerror.ParseError(map[string]any{
					"offset": 12,
				})
				return err
			},
		},
		{
			name: "invalid request",
			spec: rpcerror.Spec{
				JSONRPCCode: contract.JSONRPCInvalidRequest,
				KilnCode:    "runtime.invalid_request",
				Method:      method,
				Category:    runtime_error.ErrorKilnErrorCategoryValidation,
				Message:     "invalid request for method: " + method,
				Retryable:   false,
				Details: map[string]any{
					"received": "bad",
				},
			},
			response: func() protocol.ErrorResponse {
				err, _ := rpcerror.InvalidRequest(protocol.ID{}, method, map[string]any{
					"received": "bad",
				})
				return err
			},
		},
		{
			name: "draining",
			spec: rpcerror.Spec{
				JSONRPCCode: contract.JSONRPCInvalidRequest,
				KilnCode:    "runtime.server_draining",
				Method:      method,
				Category:    runtime_error.ErrorKilnErrorCategoryLifecycle,
				Message:     "server is draining and cannot accept new requests",
				Retryable:   false,
				Details: map[string]any{
					"received_method": method,
				},
			},
			response: func() protocol.ErrorResponse {
				err, _ := rpcerror.Draining(protocol.ID{}, method)
				return err
			},
		},
		{
			name: "shutdown",
			spec: rpcerror.Spec{
				JSONRPCCode: contract.JSONRPCInvalidRequest,
				KilnCode:    "runtime.server_shutting_down",
				Method:      method,
				Category:    runtime_error.ErrorKilnErrorCategoryShutdown,
				Message:     "server is shutting down and cannot accept new requests",
				Retryable:   false,
				Details: map[string]any{
					"received_method": method,
				},
			},
			response: func() protocol.ErrorResponse {
				err, _ := rpcerror.Shutdown(protocol.ID{}, method)
				return err
			},
		},
	}

	for _, tc := range tests {
		tc := tc
		t.Run(tc.name, func(t *testing.T) {
			t.Parallel()

			response := tc.response()
			object, kilnErr := rpcerror.MustObject(tc.spec)

			utest.AssertNotNil(t, response.Error.Data)
			utest.AssertEqual(t, response.Error.Code, tc.spec.JSONRPCCode)
			utest.AssertEqual(t, response.Error.Message, tc.spec.Message)
			if !reflect.DeepEqual(response.Error.Data, object.Data) {
				t.Fatalf(
					"response error data does not match MustObject data\nresponse: %#v\nobject: %#v",
					response.Error.Data,
					object.Data,
				)
			}
			utest.AssertEqual(t, kilnErr.Code, tc.spec.KilnCode)
			utest.AssertEqual(t, kilnErr.Category, tc.spec.Category)
			utest.AssertEqual(t, kilnErr.Message, tc.spec.Message)
			utest.AssertEqual(t, kilnErr.Retryable, tc.spec.Retryable)
			validateRuntimeErrorData(t, response.Error.Data)
		})
	}
}
