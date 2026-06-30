package protocol_test

import (
	"bytes"
	"context"
	"encoding/json"
	"strings"
	"testing"

	utest "github.com/julianstephens/go-utils/tests"

	"github.com/julianstephens/kiln/go/internal/protocol"
)

func TestPeerReceive_TableDriven(t *testing.T) {
	t.Parallel()

	tests := []struct {
		name            string
		input           string
		maxBytes        int
		want            protocol.Message
		wantErrCode     string
		wantErrContains string
	}{
		{
			name:     "receive decodes one line into typed JSON-RPC message",
			input:    "{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"repository.search\",\"params\":{\"query\":\"x\"}}\n",
			maxBytes: 1024,
			want: protocol.Request{
				JSONRPC: protocol.DEFAULT_JSONRPC_VERSION,
				ID: func() protocol.ID {
					v := int64(1)
					return protocol.ID{Number: &v}
				}(),
				Method: "repository.search",
				Params: map[string]any{"query": "x"},
			},
		},
		{
			name:            "EOF maps to RuntimeStreamClosedError",
			input:           "",
			maxBytes:        1024,
			wantErrCode:     protocol.CodeRuntimeStreamClosed,
			wantErrContains: "input stream closed",
		},
		{
			name:            "delimiter-not-found/oversize maps to frame-size error",
			input:           strings.Repeat("x", 70000),
			maxBytes:        128,
			wantErrCode:     protocol.CodeFrameTooLarge,
			wantErrContains: "exceeds maximum size",
		},
	}

	for _, tc := range tests {
		tc := tc
		t.Run(tc.name, func(t *testing.T) {
			t.Parallel()

			in := bytes.NewBufferString(tc.input)
			out := &bytes.Buffer{}
			peer := protocol.NewPeer(in, out, tc.maxBytes)

			got, err := peer.Receive(context.Background())

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
		})
	}
}

func TestPeerSend_WritesSingleNewlineTerminatedFrame(t *testing.T) {
	t.Parallel()

	out := &bytes.Buffer{}
	peer := protocol.NewPeer(bytes.NewBuffer(nil), out, 1024)

	idValue := int64(1)
	err := peer.Send(protocol.Request{
		JSONRPC: protocol.DEFAULT_JSONRPC_VERSION,
		ID:      protocol.ID{Number: &idValue},
		Method:  "repository.search",
		Params:  map[string]any{"query": "x"},
	})
	utest.RequireNoError(t, err)

	written := out.Bytes()
	utest.AssertTrue(t, len(written) > 0, "expected output bytes")
	utest.AssertTrue(t, written[len(written)-1] == '\n', "expected newline-terminated frame")
	utest.AssertEqual(t, bytes.Count(written, []byte("\n")), 1)

	trimmed := bytes.TrimSuffix(written, []byte("\n"))
	var decoded map[string]any
	utest.RequireNoError(t, json.Unmarshal(trimmed, &decoded))
	utest.AssertEqual(t, decoded["jsonrpc"].(string), protocol.DEFAULT_JSONRPC_VERSION)
	utest.AssertEqual(t, decoded["method"].(string), "repository.search")
}
