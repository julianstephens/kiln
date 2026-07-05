package runtime_test

import (
	"bytes"
	"context"
	"errors"
	"io"
	"testing"

	utest "github.com/julianstephens/go-utils/tests"

	"github.com/julianstephens/kiln/go/internal/logger"
	"github.com/julianstephens/kiln/go/internal/protocol"
	"github.com/julianstephens/kiln/go/internal/runtime"
	"github.com/julianstephens/kiln/go/internal/runtime/contract"
)

func TestRun_Preconditions_TableDriven(t *testing.T) {
	t.Parallel()

	tests := []struct {
		name    string
		cfg     runtime.Config
		wantErr *runtime.Error
	}{
		{
			name: "missing input stream returns expected error",
			cfg: runtime.Config{
				Input:  nil,
				Output: &bytes.Buffer{},
			},
			wantErr: runtime.ErrInputStreamMissing,
		},
		{
			name: "missing output stream returns expected error",
			cfg: runtime.Config{
				Input:  bytes.NewBuffer(nil),
				Output: nil,
			},
			wantErr: runtime.ErrOutputStreamMissing,
		},
		{
			name: "invalid log sink config returns expected error",
			cfg: runtime.Config{
				Input:  bytes.NewBuffer(nil),
				Output: &bytes.Buffer{},
				Logging: logger.LoggingConfig{
					Level: "info",
					Sink: logger.LogSinkConfig{
						Kind:     logger.LogSinkKindLocalFile,
						Filename: "runtime.log",
						MaxBytes: 1,
						MaxFiles: 1,
					},
				},
			},
			wantErr: &runtime.Error{
				Code:    runtime.CodeLogSinkOpenFailed,
				Message: "failed to open log sink",
			},
		},
	}

	for _, tc := range tests {
		tc := tc
		t.Run(tc.name, func(t *testing.T) {
			t.Parallel()

			err := runtime.Run(context.Background(), tc.cfg)
			utest.AssertNotNil(t, err)

			runtimeErr, ok := err.(*runtime.Error)
			utest.AssertTrue(t, ok, "expected *runtime.Error")
			if ok {
				utest.AssertEqual(t, runtimeErr.Code, tc.wantErr.Code)
				utest.AssertEqual(t, runtimeErr.Message, tc.wantErr.Message)
			}
		})
	}
}

func TestRun_RejectsNewRequestsAfterShutdownBegins(t *testing.T) {
	t.Parallel()

	previousBuildDate := contract.BuildDate
	previousBuildVersion := contract.BuildVersion
	previousBuildCommit := contract.BuildCommit
	contract.BuildDate = "2026-07-05"
	contract.BuildVersion = "0.1.0-test"
	contract.BuildCommit = "test-commit"
	t.Cleanup(func() {
		contract.BuildDate = previousBuildDate
		contract.BuildVersion = previousBuildVersion
		contract.BuildCommit = previousBuildCommit
	})

	reader, writer := io.Pipe()
	go func() {
		_, _ = writer.Write(
			[]byte(
				`{"jsonrpc":"2.0","id":"1","method":"runtime.initialize","params":{"protocol_version":"2026-07-01","schema_set_version":"1.0.0","compatibility_major":1,"client":{"name":"test-client","version":"1.0.0"}}}` + "\n",
			),
		)
		_, _ = writer.Write(
			[]byte(
				`{"jsonrpc":"2.0","id":"2","method":"runtime.shutdown","params":{"cancel_in_flight_requests":true,"reason":"test"}}` + "\n",
			),
		)
		_, _ = writer.Write([]byte(`{"jsonrpc":"2.0","id":"3","method":"runtime.health"}` + "\n"))
		_ = writer.Close()
	}()

	output := &bytes.Buffer{}
	errOutput := &bytes.Buffer{}

	err := runtime.Run(context.Background(), runtime.Config{
		Input:  reader,
		Output: output,
		Error:  errOutput,
	})

	utest.AssertNotNil(t, err)
	var protocolErr *protocol.Error
	ok := errors.As(err, &protocolErr)
	utest.AssertTrue(t, ok, "expected *protocol.Error")
	if ok {
		utest.AssertEqual(t, protocolErr.Code, protocol.CodeRuntimeStreamClosed)
	}

	peer := protocol.NewPeer(bytes.NewBuffer(output.Bytes()), &bytes.Buffer{}, protocol.DefaultMaxMessageBytes)

	firstMsg, receiveErr := peer.Receive(context.Background())
	utest.RequireNoError(t, receiveErr)
	utest.AssertTrue(t, firstMsg.IsSuccessResponse(), "initialize request should be accepted")

	secondMsg, receiveErr := peer.Receive(context.Background())
	utest.RequireNoError(t, receiveErr)
	utest.AssertTrue(t, secondMsg.IsSuccessResponse(), "shutdown request should be accepted")

	thirdMsg, receiveErr := peer.Receive(context.Background())
	utest.RequireNoError(t, receiveErr)
	utest.AssertTrue(t, thirdMsg.IsErrorResponse(), "new request should be rejected after shutdown begins")

	thirdErrResp, ok := thirdMsg.(protocol.ErrorResponse)
	utest.AssertTrue(t, ok, "expected protocol.ErrorResponse")
	if ok {
		utest.AssertEqual(t, thirdErrResp.Error.Code, contract.JSONRPCInvalidRequest)

		kilnError, hasKilnError := thirdErrResp.Error.Data["kiln_error"].(map[string]any)
		utest.AssertTrue(t, hasKilnError, "kiln_error should be object")
		if hasKilnError {
			code, hasCode := kilnError["code"].(string)
			utest.AssertTrue(t, hasCode, "kiln_error.code should be string")
			if hasCode {
				utest.AssertEqual(t, code, "runtime.server_shutting_down")
			}
		}
	}
}
