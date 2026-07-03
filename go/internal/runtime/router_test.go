package runtime_test

import (
	"context"
	"testing"

	utest "github.com/julianstephens/go-utils/tests"

	"github.com/julianstephens/kiln/go/internal/protocol"
	"github.com/julianstephens/kiln/go/internal/runtime"
	"github.com/julianstephens/kiln/go/internal/runtime/contract"
	runtime_error "github.com/julianstephens/kiln/go/schema/runtime/error"
)

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
				JSONRPC: protocol.DefaultJsonRpcVersion,
				ID:      protocol.ID{Number: &successID},
				Method:  "runtime.health",
			},
			want: &protocol.SuccessResponse{
				JSONRPC: protocol.DefaultJsonRpcVersion,
				ID:      protocol.ID{Number: &successID},
				Result:  map[string]any{"ok": true},
			},
		},
		{
			name: "unknown method returns method not found error",
			setup: func(r *runtime.Router) {
			},
			req: protocol.Request{
				JSONRPC: protocol.DefaultJsonRpcVersion,
				ID:      protocol.ID{Number: &unknownID},
				Method:  "runtime.unknown",
			},
			want: &protocol.ErrorResponse{
				JSONRPC: protocol.DefaultJsonRpcVersion,
				ID:      protocol.ID{Number: &unknownID},
				Error: protocol.ErrorObject{
					Code:    contract.JSONRPCMethodNotFound,
					Message: "Method not found",
					Data: runtime_error.ErrorKilnError{
						Code:     "runtime.method_not_found",
						Category: "compatibility",
						Message:  "Method not found",
						Details: map[string]any{
							"requested_method": "runtime.unknown",
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
				JSONRPC: protocol.DefaultJsonRpcVersion,
				ID:      protocol.ID{Number: &nilHandlerID},
				Method:  "runtime.health",
				Params: map[string]any{
					"probe": true,
				},
			},
			want: &protocol.ErrorResponse{
				JSONRPC: protocol.DefaultJsonRpcVersion,
				ID:      protocol.ID{Number: &nilHandlerID},
				Error: protocol.ErrorObject{
					Code:    contract.JSONRPCInternalError,
					Message: "Handler returned nil",
					Data: runtime_error.ErrorKilnError{
						Code:     "runtime.internal_error",
						Category: "internal",
						Message:  "Handler returned nil response",
						Details: map[string]any{
							"requested_method": "runtime.health",
							"request_params": map[string]any{
								"probe": true,
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
			utest.AssertDeepEqual(t, got, tc.want)
		})
	}
}
