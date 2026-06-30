package protocol_test

import (
	"bytes"
	"encoding/json"
	"testing"

	utest "github.com/julianstephens/go-utils/tests"

	"github.com/julianstephens/kiln/go/internal/protocol"
)

func TestDecodeFrame_TableDriven(t *testing.T) {
	t.Parallel()

	tests := []struct {
		name             string
		frame            []byte
		maxBytes         int
		want             protocol.JSONObject
		wantErrCode      string
		wantErrContains  string
		wantErrIsNewline bool
	}{
		{
			name:     "valid JSON object returned unchanged",
			frame:    []byte(`{"kind":"request","status":"ok","active":true}`),
			maxBytes: protocol.DefaultMaxMessageBytes,
			want: protocol.JSONObject{
				"kind":   "request",
				"status": "ok",
				"active": true,
			},
		},
		{
			name:            "oversized bytes rejected",
			frame:           []byte(`{"a":1}`),
			maxBytes:        2,
			wantErrCode:     protocol.CodeFrameTooLarge,
			wantErrContains: "exceeds maximum size",
		},
		{
			name:             "embedded newline rejected",
			frame:            []byte("{\"a\":1}\n"),
			maxBytes:         protocol.DefaultMaxMessageBytes,
			wantErrCode:      protocol.CodeInvalidFrame,
			wantErrContains:  "newline character",
			wantErrIsNewline: true,
		},
		{
			name:            "malformed JSON rejected",
			frame:           []byte(`{"a":`),
			maxBytes:        protocol.DefaultMaxMessageBytes,
			wantErrCode:     protocol.CodeFramingError,
			wantErrContains: "invalid JSON",
		},
		{
			name:            "non-object JSON rejected",
			frame:           []byte(`[1,2,3]`),
			maxBytes:        protocol.DefaultMaxMessageBytes,
			wantErrCode:     protocol.CodeFramingError,
			wantErrContains: "expected JSON object",
		},
	}

	for _, tc := range tests {
		tc := tc
		t.Run(tc.name, func(t *testing.T) {
			t.Parallel()

			got, err := protocol.DecodeFrame(tc.frame, tc.maxBytes)

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

			if tc.wantErrContains != "" {
				utest.AssertErrorContains(t, err, tc.wantErrContains)
			}

			if tc.wantErrIsNewline {
				utest.AssertErrorIs(t, err, protocol.ErrEmbeddedNewline)
			}

			utest.AssertNil(t, got)
		})
	}
}

func TestEncodeFrame_TableDriven(t *testing.T) {
	t.Parallel()

	tests := []struct {
		name            string
		obj             protocol.JSONObject
		want            protocol.JSONObject
		wantErrCode     string
		wantErrContains string
	}{
		{
			name: "valid object",
			obj: protocol.JSONObject{
				"answer": 42,
			},
			want: protocol.JSONObject{
				"answer": float64(42),
			},
		},
		{
			name: "marshal error",
			obj: protocol.JSONObject{
				"bad": func() {},
			},
			wantErrCode:     protocol.CodeFramingError,
			wantErrContains: "unsupported type",
		},
	}

	for _, tc := range tests {
		tc := tc
		t.Run(tc.name, func(t *testing.T) {
			t.Parallel()

			got, err := protocol.EncodeFrame(tc.obj)

			if tc.wantErrCode == "" {
				utest.RequireNoError(t, err)
				utest.AssertTrue(t, bytes.HasSuffix(got, []byte("\n")), "expected encoded frame to end with newline")

				trimmed := bytes.TrimSuffix(got, []byte("\n"))
				var decoded protocol.JSONObject
				utest.RequireNoError(t, json.Unmarshal(trimmed, &decoded))
				utest.AssertDeepEqual(t, decoded, tc.want)
				return
			}

			utest.AssertNotNil(t, err)
			perr, ok := err.(*protocol.Error)
			utest.AssertTrue(t, ok, "expected *protocol.Error")
			if ok {
				utest.AssertEqual(t, perr.Code, tc.wantErrCode)
			}

			if tc.wantErrContains != "" {
				utest.AssertErrorContains(t, err, tc.wantErrContains)
			}

			utest.AssertTrue(t, len(got) == 0, "expected no encoded frame on error")
		})
	}
}
