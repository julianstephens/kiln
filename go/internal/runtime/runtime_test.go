package runtime_test

import (
	"bytes"
	"context"
	"io"
	"testing"

	utest "github.com/julianstephens/go-utils/tests"

	"github.com/julianstephens/kiln/go/internal/logger"
	"github.com/julianstephens/kiln/go/internal/persistence"
	"github.com/julianstephens/kiln/go/internal/protocol"
	"github.com/julianstephens/kiln/go/internal/runtime"
	"github.com/julianstephens/kiln/go/internal/runtime/contract"
)

func TestRun_Preconditions_TableDriven(t *testing.T) {
	t.Parallel()

	// Set up build info for tests that need it
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
			if tc.wantErr == nil {
				utest.RequireNoError(t, err)
				return
			}

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

func TestRun_PersistenceStartupFailureLeavesRuntimeNotReady(t *testing.T) {
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
		_, _ = writer.Write([]byte(`{"jsonrpc":"2.0","id":"2","method":"runtime.health"}` + "\n"))
		_, _ = writer.Write(
			[]byte(
				`{"jsonrpc":"2.0","id":"3","method":"runtime.shutdown","params":{"cancel_in_flight_requests":true,"reason":"test"}}` + "\n",
			),
		)
		_ = writer.Close()
	}()

	output := &bytes.Buffer{}

	err := runtime.Run(context.Background(), runtime.Config{
		Input:  reader,
		Output: output,
		DB: persistence.Config{
			DBType:                       "invalid-store",
			InstallationDBPath:           ":memory:",
			MaxOpenConnections:           1,
			MaxIdleConnections:           1,
			MaxConnectionLifetimeSeconds: 1,
		},
	})
	utest.RequireNoError(t, err)

	peer := protocol.NewPeer(bytes.NewBuffer(output.Bytes()), &bytes.Buffer{}, protocol.DefaultMaxMessageBytes)

	firstMsg, receiveErr := peer.Receive(context.Background())
	utest.RequireNoError(t, receiveErr)
	utest.AssertTrue(t, firstMsg.IsSuccessResponse(), "initialize request should be accepted")

	secondMsg, receiveErr := peer.Receive(context.Background())
	utest.RequireNoError(t, receiveErr)
	utest.AssertTrue(t, secondMsg.IsSuccessResponse(), "health request should be accepted")

	healthResp, ok := secondMsg.(protocol.SuccessResponse)
	utest.AssertTrue(t, ok, "expected success response")
	if ok {
		ready, readyOK := healthResp.Result["ready"].(bool)
		utest.AssertTrue(t, readyOK, "health.ready should be bool")
		utest.AssertEqual(t, ready, false)

		initialized, initializedOK := healthResp.Result["initialized"].(bool)
		utest.AssertTrue(t, initializedOK, "health.initialized should be bool")
		utest.AssertEqual(t, initialized, true)

		fatal, fatalOK := healthResp.Result["last_fatal_startup_error"].(map[string]any)
		utest.AssertTrue(t, fatalOK, "health.last_fatal_startup_error should be object")
		if fatalOK {
			code, codeOK := fatal["code"].(string)
			utest.AssertTrue(t, codeOK, "fatal error code should be string")
			utest.AssertEqual(t, code, "persistence.store_open_failed")

			message, messageOK := fatal["message"].(string)
			utest.AssertTrue(t, messageOK, "fatal error message should be string")
			utest.AssertEqual(t, message, "failed to open store at path: :memory:")
		}
	}

	thirdMsg, receiveErr := peer.Receive(context.Background())
	utest.RequireNoError(t, receiveErr)
	utest.AssertTrue(t, thirdMsg.IsSuccessResponse(), "shutdown request should be accepted")
}

func TestRun_RejectsNewRequestsAfterShutdownBegins(t *testing.T) {
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
		DB: persistence.Config{
			DBType:                       persistence.SqliteStoreKind,
			InstallationDBPath:           ":memory:",
			MaxOpenConnections:           1,
			MaxIdleConnections:           1,
			MaxConnectionLifetimeSeconds: 1,
		},
	})
	utest.RequireNoError(t, err)

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
