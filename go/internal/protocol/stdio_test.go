package protocol_test

import (
	"bytes"
	"context"
	"encoding/json"
	"io"
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
				JSONRPC: protocol.DefaultJSONRPCVersion,
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

	stringID := "req-1"
	numericID := int64(1)
	nullID := protocol.ID{Null: true}

	tests := []struct {
		name   string
		msg    protocol.Message
		wantID any
	}{
		{
			name: "id number encoded as 1",
			msg: protocol.Request{
				JSONRPC: protocol.DefaultJSONRPCVersion,
				ID:      protocol.ID{Number: &numericID},
				Method:  "repository.search",
				Params:  map[string]any{"query": "x"},
			},
			wantID: float64(1),
		},
		{
			name: "id string encoded as req-1",
			msg: protocol.Request{
				JSONRPC: protocol.DefaultJSONRPCVersion,
				ID:      protocol.ID{String: &stringID},
				Method:  "repository.search",
				Params:  map[string]any{"query": "x"},
			},
			wantID: "req-1",
		},
		{
			name: "error response id null encoded as null",
			msg: protocol.ErrorResponse{
				JSONRPC: protocol.DefaultJSONRPCVersion,
				ID:      nullID,
				Error: protocol.ErrorObject{
					Code:    -32000,
					Message: "something failed",
				},
			},
			wantID: nil,
		},
	}

	for _, tc := range tests {
		tc := tc
		t.Run(tc.name, func(t *testing.T) {
			t.Parallel()

			out := &bytes.Buffer{}
			peer := protocol.NewPeer(bytes.NewBuffer(nil), out, 1024)

			err := peer.Send(tc.msg)
			utest.RequireNoError(t, err)

			written := out.Bytes()
			utest.AssertTrue(t, len(written) > 0, "expected output bytes")
			utest.AssertTrue(t, written[len(written)-1] == '\n', "expected newline-terminated frame")
			utest.AssertEqual(t, bytes.Count(written, []byte("\n")), 1)

			trimmed := bytes.TrimSuffix(written, []byte("\n"))
			var decoded map[string]any
			utest.RequireNoError(t, json.Unmarshal(trimmed, &decoded))
			utest.AssertEqual(t, decoded["jsonrpc"].(string), protocol.DefaultJSONRPCVersion)
			utest.AssertDeepEqual(t, decoded["id"], tc.wantID)
		})
	}
}

func TestPeerReceive_RejectsPartialFrameBeforeDelimiter(t *testing.T) {
	t.Parallel()

	in := bytes.NewBufferString(`{"jsonrpc":"2.0","id":1,"method":"repository.search","params":{"query":"x"}}`)
	out := &bytes.Buffer{}
	peer := protocol.NewPeer(in, out, 1024)

	got, err := peer.Receive(context.Background())

	utest.AssertNil(t, got)
	utest.AssertNotNil(t, err)
	perr, ok := err.(*protocol.Error)
	utest.AssertTrue(t, ok, "expected *protocol.Error")
	if ok {
		utest.AssertEqual(t, perr.Code, protocol.CodeReadStreamError)
	}
	utest.AssertErrorContains(t, err, "partial frame before EOF")
}

func TestPeerReceive_ReadsTwoFramesFromOneStream(t *testing.T) {
	t.Parallel()

	input := strings.Join([]string{
		`{"jsonrpc":"2.0","id":1,"method":"repository.search","params":{"query":"first"}}`,
		`{"jsonrpc":"2.0","id":2,"method":"repository.search","params":{"query":"second"}}`,
	}, "\n") + "\n"

	peer := protocol.NewPeer(bytes.NewBufferString(input), &bytes.Buffer{}, 1024)

	first, err := peer.Receive(context.Background())
	utest.RequireNoError(t, err)

	second, err := peer.Receive(context.Background())
	utest.RequireNoError(t, err)

	firstID := int64(1)
	secondID := int64(2)
	utest.AssertDeepEqual(t, first, protocol.Request{
		JSONRPC: protocol.DefaultJSONRPCVersion,
		ID:      protocol.ID{Number: &firstID},
		Method:  "repository.search",
		Params:  map[string]any{"query": "first"},
	})
	utest.AssertDeepEqual(t, second, protocol.Request{
		JSONRPC: protocol.DefaultJSONRPCVersion,
		ID:      protocol.ID{Number: &secondID},
		Method:  "repository.search",
		Params:  map[string]any{"query": "second"},
	})
}

func TestPeerReceive_ReassemblesPartialChunksIntoOneFrame(t *testing.T) {
	t.Parallel()

	chunked := &chunkedReader{
		chunks: []string{
			`{"jsonrpc":"2.0",`,
			`"id":1,`,
			`"method":"repository.search",`,
			`"params":{"query":"chunked"}}`,
			"\n",
		},
	}

	peer := protocol.NewPeer(chunked, &bytes.Buffer{}, 1024)
	got, err := peer.Receive(context.Background())
	utest.RequireNoError(t, err)

	id := int64(1)
	utest.AssertDeepEqual(t, got, protocol.Request{
		JSONRPC: protocol.DefaultJSONRPCVersion,
		ID:      protocol.ID{Number: &id},
		Method:  "repository.search",
		Params:  map[string]any{"query": "chunked"},
	})
}

func TestPeerReceive_RejectsOversizedFrameBeforeJSONDecode(t *testing.T) {
	t.Parallel()

	input := strings.Repeat("x", 129) + "\n"
	peer := protocol.NewPeer(bytes.NewBufferString(input), &bytes.Buffer{}, 128)

	got, err := peer.Receive(context.Background())

	utest.AssertNil(t, got)
	utest.AssertNotNil(t, err)
	perr, ok := err.(*protocol.Error)
	utest.AssertTrue(t, ok, "expected *protocol.Error")
	if ok {
		utest.AssertEqual(t, perr.Code, protocol.CodeFrameTooLarge)
	}
	utest.AssertErrorContains(t, err, "exceeds maximum size")
}

type chunkedReader struct {
	chunks []string
	index  int
	offset int
}

func (r *chunkedReader) Read(p []byte) (int, error) {
	if r.index >= len(r.chunks) {
		return 0, io.EOF
	}

	chunk := r.chunks[r.index]
	if r.offset >= len(chunk) {
		r.index++
		r.offset = 0
		return r.Read(p)
	}

	n := copy(p, chunk[r.offset:])
	r.offset += n
	if r.offset >= len(chunk) {
		r.index++
		r.offset = 0
	}
	return n, nil
}
