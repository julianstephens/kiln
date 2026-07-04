package protocol_test

import (
	"testing"

	utest "github.com/julianstephens/go-utils/tests"

	"github.com/julianstephens/kiln/go/internal/protocol"
)

func TestParseMessage_TableDriven(t *testing.T) {
	t.Parallel()

	requestID := int64(42)
	unknownMethodID := int64(7)
	successID := int64(99)

	tests := []struct {
		name            string
		raw             map[string]any
		want            protocol.Message
		wantErrCode     string
		wantErrContains string
	}{
		{
			name: "valid request accepted",
			raw: map[string]any{
				"jsonrpc": protocol.DefaultJSONRPCVersion,
				"id":      float64(42),
				"method":  "repository.search",
				"params": map[string]any{
					"query": "schema generator",
				},
			},
			want: protocol.Request{
				JSONRPC: protocol.DefaultJSONRPCVersion,
				ID:      protocol.ID{Number: &requestID},
				Method:  "repository.search",
				Params: map[string]any{
					"query": "schema generator",
				},
			},
		},
		{
			name: "unknown method request accepted as JSON-RPC",
			raw: map[string]any{
				"jsonrpc": protocol.DefaultJSONRPCVersion,
				"id":      float64(7),
				"method":  "custom.unknown",
			},
			want: protocol.Request{
				JSONRPC: protocol.DefaultJSONRPCVersion,
				ID:      protocol.ID{Number: &unknownMethodID},
				Method:  "custom.unknown",
			},
		},
		{
			name: "success response without method accepted",
			raw: map[string]any{
				"jsonrpc": protocol.DefaultJSONRPCVersion,
				"id":      float64(99),
				"result": map[string]any{
					"ok": true,
				},
			},
			want: protocol.SuccessResponse{
				JSONRPC: protocol.DefaultJSONRPCVersion,
				ID:      protocol.ID{Number: &successID},
				Result: map[string]any{
					"ok": true,
				},
			},
		},
		{
			name: "error response with id null accepted",
			raw: map[string]any{
				"jsonrpc": protocol.DefaultJSONRPCVersion,
				"id":      nil,
				"error": map[string]any{
					"code":    float64(-32000),
					"message": "something failed",
					"data": map[string]any{
						"detail": "oops",
					},
				},
			},
			want: protocol.ErrorResponse{
				JSONRPC: protocol.DefaultJSONRPCVersion,
				ID:      protocol.ID{Null: true},
				Error: protocol.ErrorObject{
					Code:    -32000,
					Message: "something failed",
					Data: map[string]any{
						"detail": "oops",
					},
				},
			},
		},
		{
			name: "result + error together rejected",
			raw: map[string]any{
				"jsonrpc": protocol.DefaultJSONRPCVersion,
				"id":      float64(1),
				"result":  map[string]any{},
				"error": map[string]any{
					"code":    float64(-1),
					"message": "bad",
				},
			},
			wantErrCode:     protocol.CodeInvalidJSONRPCFrame,
			wantErrContains: "response must not include both result and error",
		},
		{
			name: "params without method rejected",
			raw: map[string]any{
				"jsonrpc": protocol.DefaultJSONRPCVersion,
				"id":      float64(1),
				"params":  map[string]any{},
			},
			wantErrCode:     protocol.CodeInvalidJSONRPCFrame,
			wantErrContains: "params field is only valid for requests",
		},
	}

	for _, tc := range tests {
		tc := tc
		t.Run(tc.name, func(t *testing.T) {
			t.Parallel()

			got, err := protocol.ParseMessage(tc.raw)

			if tc.wantErrCode == "" {
				utest.RequireNoError(t, err)
				utest.AssertDeepEqual(t, got, tc.want)
				return
			}

			utest.AssertNotNil(t, err)
			perr, ok := err.(*protocol.Error)
			utest.AssertTrue(t, ok, "expected *protocol.Error")
			if ok {
				utest.AssertEqual(t, perr.Code, tc.wantErrCode)
			}
			utest.AssertErrorContains(t, err, tc.wantErrContains)
			utest.AssertNil(t, got)
		})
	}
}

func TestParseMessage_ErrorPaths_TableDriven(t *testing.T) {
	t.Parallel()

	tests := []struct {
		name            string
		raw             map[string]any
		wantErrContains string
	}{
		{
			name: "missing jsonrpc field",
			raw: map[string]any{
				"id":     float64(1),
				"method": "repository.search",
			},
			wantErrContains: "invalid or missing jsonrpc field",
		},
		{
			name: "request id missing",
			raw: map[string]any{
				"jsonrpc": protocol.DefaultJSONRPCVersion,
				"method":  "repository.search",
			},
			wantErrContains: "request id is required",
		},
		{
			name: "request id null",
			raw: map[string]any{
				"jsonrpc": protocol.DefaultJSONRPCVersion,
				"id":      nil,
				"method":  "repository.search",
			},
			wantErrContains: "request id is required",
		},
		{
			name: "request id invalid type",
			raw: map[string]any{
				"jsonrpc": protocol.DefaultJSONRPCVersion,
				"id":      true,
				"method":  "repository.search",
			},
			wantErrContains: "request id must be string or number",
		},
		{
			name: "request fractional id rejected",
			raw: map[string]any{
				"jsonrpc": protocol.DefaultJSONRPCVersion,
				"id":      1.25,
				"method":  "repository.search",
			},
			wantErrContains: "request id must be string or number",
		},
		{
			name: "request method empty",
			raw: map[string]any{
				"jsonrpc": protocol.DefaultJSONRPCVersion,
				"id":      float64(1),
				"method":  "",
			},
			wantErrContains: "method must be a non-empty string",
		},
		{
			name: "request params wrong type",
			raw: map[string]any{
				"jsonrpc": protocol.DefaultJSONRPCVersion,
				"id":      float64(1),
				"method":  "repository.search",
				"params":  []any{},
			},
			wantErrContains: "params must be a JSON object",
		},
		{
			name: "success response id missing",
			raw: map[string]any{
				"jsonrpc": protocol.DefaultJSONRPCVersion,
				"result":  map[string]any{},
			},
			wantErrContains: "success response id is required",
		},
		{
			name: "success response id invalid type",
			raw: map[string]any{
				"jsonrpc": protocol.DefaultJSONRPCVersion,
				"id":      true,
				"result":  map[string]any{},
			},
			wantErrContains: "success response id must be string or number",
		},
		{
			name: "success response fractional id rejected",
			raw: map[string]any{
				"jsonrpc": protocol.DefaultJSONRPCVersion,
				"id":      1.25,
				"result":  map[string]any{},
			},
			wantErrContains: "success response id must be string or number",
		},
		{
			name: "success response result wrong type",
			raw: map[string]any{
				"jsonrpc": protocol.DefaultJSONRPCVersion,
				"id":      float64(1),
				"result":  []any{},
			},
			wantErrContains: "result must be a JSON object",
		},
		{
			name: "error response missing id field",
			raw: map[string]any{
				"jsonrpc": protocol.DefaultJSONRPCVersion,
				"error": map[string]any{
					"code":    float64(-1),
					"message": "bad",
				},
			},
			wantErrContains: "error response id field is required, but may be null",
		},
		{
			name: "error response id invalid type",
			raw: map[string]any{
				"jsonrpc": protocol.DefaultJSONRPCVersion,
				"id":      true,
				"error": map[string]any{
					"code":    float64(-1),
					"message": "bad",
				},
			},
			wantErrContains: "error response id must be string, number, or null",
		},
		{
			name: "error response fractional id rejected",
			raw: map[string]any{
				"jsonrpc": protocol.DefaultJSONRPCVersion,
				"id":      1.25,
				"error": map[string]any{
					"code":    float64(-1),
					"message": "bad",
				},
			},
			wantErrContains: "error response id must be string, number, or null",
		},
		{
			name: "error object wrong type",
			raw: map[string]any{
				"jsonrpc": protocol.DefaultJSONRPCVersion,
				"id":      float64(1),
				"error":   "boom",
			},
			wantErrContains: "error must be a JSON object",
		},
		{
			name: "error code non-integer",
			raw: map[string]any{
				"jsonrpc": protocol.DefaultJSONRPCVersion,
				"id":      float64(1),
				"error": map[string]any{
					"code":    1.25,
					"message": "bad",
				},
			},
			wantErrContains: "error.code must be an integer",
		},
		{
			name: "error message empty",
			raw: map[string]any{
				"jsonrpc": protocol.DefaultJSONRPCVersion,
				"id":      float64(1),
				"error": map[string]any{
					"code":    float64(-1),
					"message": "",
				},
			},
			wantErrContains: "error.message must be a non-empty string",
		},
		{
			name: "error data wrong type",
			raw: map[string]any{
				"jsonrpc": protocol.DefaultJSONRPCVersion,
				"id":      float64(1),
				"error": map[string]any{
					"code":    float64(-1),
					"message": "bad",
					"data":    []any{"x"},
				},
			},
			wantErrContains: "error.data must be a JSON object when present",
		},
	}

	for _, tc := range tests {
		tc := tc
		t.Run(tc.name, func(t *testing.T) {
			t.Parallel()

			got, err := protocol.ParseMessage(tc.raw)

			utest.AssertNotNil(t, err)
			_ = got

			perr, ok := err.(*protocol.Error)
			utest.AssertTrue(t, ok, "expected *protocol.Error")
			if ok {
				utest.AssertEqual(t, perr.Code, protocol.CodeInvalidJSONRPCFrame)
			}

			utest.AssertErrorContains(t, err, tc.wantErrContains)
		})
	}
}
