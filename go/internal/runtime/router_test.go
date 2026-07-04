package runtime_test

import (
	"context"
	"reflect"
	"testing"

	utest "github.com/julianstephens/go-utils/tests"

	"github.com/julianstephens/kiln/go/internal/protocol"
	"github.com/julianstephens/kiln/go/internal/runtime"
	"github.com/julianstephens/kiln/go/internal/runtime/contract"
)

func anyStrings(values []string) []any {
	result := make([]any, len(values))
	for i, value := range values {
		result[i] = value
	}
	return result
}

func TestRouterDispatch_TableDriven(t *testing.T) {
	t.Parallel()

	successID := int64(42)
	unknownID := int64(99)
	nilHandlerID := int64(77)

	tests := []struct {
		name  string
		setup func(*runtime.Router)
		req   protocol.Request
		want  protocol.Message
	}{
		{
			name: "registered handler returns message",
			setup: func(r *runtime.Router) {
				r.Register("runtime.health", func(ctx context.Context, req protocol.Request) protocol.Message {
					return protocol.NewSuccessResponse(req.ID, map[string]any{"ok": true})
				})
			},
			req: protocol.Request{
				JSONRPC: protocol.DefaultJSONRPCVersion,
				ID:      protocol.ID{Number: &successID},
				Method:  "runtime.health",
			},
			want: &protocol.SuccessResponse{
				JSONRPC: protocol.DefaultJSONRPCVersion,
				ID:      protocol.ID{Number: &successID},
				Result:  map[string]any{"ok": true},
			},
		},
		{
			name: "unknown method returns method not found error",
			setup: func(r *runtime.Router) {
			},
			req: protocol.Request{
				JSONRPC: protocol.DefaultJSONRPCVersion,
				ID:      protocol.ID{Number: &unknownID},
				Method:  "runtime.unknown",
			},
			want: protocol.ErrorResponse{
				JSONRPC: protocol.DefaultJSONRPCVersion,
				ID:      protocol.ID{Number: &unknownID},
				Error: protocol.ErrorObject{
					Code:    contract.JSONRPCMethodNotFound,
					Message: "method_not_found: runtime.unknown",
					Data: map[string]any{
						"kiln_error": map[string]any{
							"code":      "runtime.method_not_found",
							"category":  "validation",
							"message":   "method_not_found: runtime.unknown",
							"retryable": false,
							"details": map[string]any{
								"received_method":             "runtime.unknown",
								"supported_methods":           anyStrings(protocol.SupportedMethods()),
								"supported_method_namespaces": anyStrings(protocol.SupportedMethodNamespaces()),
							},
						},
					},
				},
			},
		},
		{
			name: "nil handler response returns internal error",
			setup: func(r *runtime.Router) {
				r.Register("runtime.health", func(ctx context.Context, req protocol.Request) protocol.Message {
					return nil
				})
			},
			req: protocol.Request{
				JSONRPC: protocol.DefaultJSONRPCVersion,
				ID:      protocol.ID{Number: &nilHandlerID},
				Method:  "runtime.health",
				Params: map[string]any{
					"probe": true,
				},
			},
			want: protocol.ErrorResponse{
				JSONRPC: protocol.DefaultJSONRPCVersion,
				ID:      protocol.ID{Number: &nilHandlerID},
				Error: protocol.ErrorObject{
					Code:    contract.JSONRPCInternalError,
					Message: "Handler returned nil response",
					Data: map[string]any{
						"kiln_error": map[string]any{
							"code":      "runtime.internal_error",
							"category":  "internal",
							"message":   "Handler returned nil response",
							"retryable": false,
							"details": map[string]any{
								"requested_method": "runtime.health",
								"request_params": map[string]any{
									"probe": true,
								},
							},
						},
					},
				},
			},
		},
	}

	for _, tc := range tests {
		tc := tc
		t.Run(tc.name, func(t *testing.T) {
			t.Parallel()

			router := runtime.NewRouter()
			tc.setup(router)

			got := router.Dispatch(context.Background(), tc.req)

			switch want := tc.want.(type) {
			case *protocol.SuccessResponse:
				gotResp, ok := got.(*protocol.SuccessResponse)
				utest.AssertTrue(t, ok, "expected success response")
				utest.AssertEqual(t, gotResp.JSONRPC, want.JSONRPC)
				if !reflect.DeepEqual(gotResp.ID, want.ID) {
					t.Fatalf("success id mismatch: got %#v want %#v", gotResp.ID, want.ID)
				}
				if !reflect.DeepEqual(gotResp.Result, want.Result) {
					t.Fatalf("success result mismatch: got %#v want %#v", gotResp.Result, want.Result)
				}
			case protocol.ErrorResponse:
				gotResp, ok := got.(protocol.ErrorResponse)
				utest.AssertTrue(t, ok, "expected error response")
				utest.AssertEqual(t, gotResp.JSONRPC, want.JSONRPC)
				if !reflect.DeepEqual(gotResp.ID, want.ID) {
					t.Fatalf("error id mismatch: got %#v want %#v", gotResp.ID, want.ID)
				}
				utest.AssertEqual(t, gotResp.Error.Code, want.Error.Code)
				utest.AssertEqual(t, gotResp.Error.Message, want.Error.Message)
				if !reflect.DeepEqual(gotResp.Error.Data, want.Error.Data) {
					t.Fatalf("error data mismatch: got %#v want %#v", gotResp.Error.Data, want.Error.Data)
				}
			default:
				t.Fatalf("unexpected want type %T", tc.want)
			}
		})
	}
}
