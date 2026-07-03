package handler_test

import (
	"context"
	"testing"

	utest "github.com/julianstephens/go-utils/tests"

	"github.com/julianstephens/kiln/go/internal/protocol"
	"github.com/julianstephens/kiln/go/internal/runtime/contract"
	"github.com/julianstephens/kiln/go/internal/runtime/handler"
	runtime_error "github.com/julianstephens/kiln/go/schema/runtime/error"
)

// TestMakeInitializeHandler_InvalidParams tests that initialize handler returns error for invalid params
func TestMakeInitializeHandler_InvalidParams(t *testing.T) {
	t.Parallel()

	state := &handler.HandlerState{}
	deps := &contract.RuntimeDeps{
		Build: contract.BuildInfo{
			Version: "0.1.0",
			Commit:  "abc123",
		},
	}

	initHandler := handler.MakeInitializeHandler(state, deps)
	requestID := int64(1)

	req := protocol.Request{
		JSONRPC: protocol.DefaultJSONRPCVersion,
		ID:      protocol.ID{Number: &requestID},
		Method:  "runtime.initialize",
		Params:  map[string]any{},
	}

	resp := initHandler(context.Background(), req)
	utest.AssertTrue(t, resp.IsErrorResponse(), "expected error response for invalid params")

	errResp := resp.(*protocol.ErrorResponse)
	utest.AssertEqual(t, errResp.Error.Code, contract.JSONRPCInvalidParams)
	utest.AssertEqual(t, errResp.Error.Data.KilnError.Code, "runtime.invalid_initialize_params")
	utest.AssertNotNil(t, state.LastFatalStartupError, "fatal error should be stored in state")
}

// TestMakeHealthHandler_Ready tests health handler when runtime is ready
func TestMakeHealthHandler_Ready(t *testing.T) {
	t.Parallel()

	state := &handler.HandlerState{}
	state.Ready = true
	state.Initialized = true

	healthHandler := handler.MakeHealthHandler(state)
	requestID := int64(10)

	req := protocol.Request{
		JSONRPC: protocol.DefaultJSONRPCVersion,
		ID:      protocol.ID{Number: &requestID},
		Method:  "runtime.health",
	}

	resp := healthHandler(context.Background(), req)
	utest.AssertTrue(t, resp.IsSuccessResponse(), "health should return success response")

	successResp := resp.(*protocol.SuccessResponse)
	result := successResp.Result

	readyVal, ok := result["ready"].(bool)
	utest.AssertTrue(t, ok, "ready should be bool")
	utest.AssertEqual(t, readyVal, true)

	initVal, ok := result["initialized"].(bool)
	utest.AssertTrue(t, ok, "initialized should be bool")
	utest.AssertEqual(t, initVal, true)
}

// TestMakeHealthHandler_NotReady tests health handler when runtime is not ready
func TestMakeHealthHandler_NotReady(t *testing.T) {
	t.Parallel()

	state := &handler.HandlerState{}
	state.Ready = false
	state.Initialized = true

	healthHandler := handler.MakeHealthHandler(state)
	requestID := int64(11)

	req := protocol.Request{
		JSONRPC: protocol.DefaultJSONRPCVersion,
		ID:      protocol.ID{Number: &requestID},
		Method:  "runtime.health",
	}

	resp := healthHandler(context.Background(), req)
	utest.AssertTrue(t, resp.IsSuccessResponse(), "health should return success response")

	successResp := resp.(*protocol.SuccessResponse)
	result := successResp.Result

	readyVal, ok := result["ready"].(bool)
	utest.AssertTrue(t, ok, "ready should be bool")
	utest.AssertEqual(t, readyVal, false)

	initVal, ok := result["initialized"].(bool)
	utest.AssertTrue(t, ok, "initialized should be bool")
	utest.AssertEqual(t, initVal, true)
}

// TestMakeHealthHandler_AfterShutdown tests health handler after shutdown
func TestMakeHealthHandler_AfterShutdown(t *testing.T) {
	t.Parallel()

	state := &handler.HandlerState{}
	state.Ready = false
	state.Shutdown = true
	state.Initialized = true

	healthHandler := handler.MakeHealthHandler(state)
	requestID := int64(12)

	req := protocol.Request{
		JSONRPC: protocol.DefaultJSONRPCVersion,
		ID:      protocol.ID{Number: &requestID},
		Method:  "runtime.health",
	}

	resp := healthHandler(context.Background(), req)
	utest.AssertTrue(t, resp.IsSuccessResponse(), "health should return success response")

	successResp := resp.(*protocol.SuccessResponse)
	result := successResp.Result

	shutdownVal, ok := result["shutdown"].(bool)
	utest.AssertTrue(t, ok, "shutdown should be bool")
	utest.AssertEqual(t, shutdownVal, true)

	readyVal, ok := result["ready"].(bool)
	utest.AssertTrue(t, ok, "ready should be bool")
	utest.AssertEqual(t, readyVal, false)
}

// TestMakeHealthHandler_NotInitialized tests health handler when not initialized
func TestMakeHealthHandler_NotInitialized(t *testing.T) {
	t.Parallel()

	state := &handler.HandlerState{}

	healthHandler := handler.MakeHealthHandler(state)
	requestID := int64(13)

	req := protocol.Request{
		JSONRPC: protocol.DefaultJSONRPCVersion,
		ID:      protocol.ID{Number: &requestID},
		Method:  "runtime.health",
	}

	resp := healthHandler(context.Background(), req)
	utest.AssertTrue(t, resp.IsSuccessResponse(), "health should return success response")

	successResp := resp.(*protocol.SuccessResponse)
	result := successResp.Result

	initVal, ok := result["initialized"].(bool)
	utest.AssertTrue(t, ok, "initialized should be bool")
	utest.AssertEqual(t, initVal, false)

	readyVal, ok := result["ready"].(bool)
	utest.AssertTrue(t, ok, "ready should be bool")
	utest.AssertEqual(t, readyVal, false)
}

// TestMakeHealthHandler_WithFatalError tests health handler with fatal error
func TestMakeHealthHandler_WithFatalError(t *testing.T) {
	t.Parallel()

	state := &handler.HandlerState{}
	state.Initialized = true
	state.Ready = false

	fatalErr := &runtime_error.ErrorKilnError{
		Code:      "runtime.startup_failed",
		Category:  "internal",
		Message:   "Failed to start",
		Retryable: false,
	}
	state.LastFatalStartupError = fatalErr

	healthHandler := handler.MakeHealthHandler(state)
	requestID := int64(14)

	req := protocol.Request{
		JSONRPC: protocol.DefaultJSONRPCVersion,
		ID:      protocol.ID{Number: &requestID},
		Method:  "runtime.health",
	}

	resp := healthHandler(context.Background(), req)
	utest.AssertTrue(t, resp.IsSuccessResponse(), "health should return success response")

	successResp := resp.(*protocol.SuccessResponse)
	result := successResp.Result

	fatalErrVal, exists := result["last_fatal_startup_error"]
	utest.AssertTrue(t, exists, "last_fatal_startup_error key should exist")
	utest.AssertNotNil(t, fatalErrVal, "last_fatal_startup_error should not be nil")
}
