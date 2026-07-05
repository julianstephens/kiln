package handler_test

import (
	"context"
	"testing"
	"time"

	utest "github.com/julianstephens/go-utils/tests"

	"github.com/julianstephens/kiln/go/internal/protocol"
	"github.com/julianstephens/kiln/go/internal/runtime/contract"
	"github.com/julianstephens/kiln/go/internal/runtime/handler"
	runtime_error "github.com/julianstephens/kiln/go/schema/runtime/error"
)

func waitForCondition(t *testing.T, timeout time.Duration, condition func() bool) {
	t.Helper()

	deadline := time.Now().Add(timeout)
	for time.Now().Before(deadline) {
		if condition() {
			return
		}
		time.Sleep(10 * time.Millisecond)
	}

	t.Fatalf("condition not met within %s", timeout)
}

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

	errResp := resp.(protocol.ErrorResponse)
	utest.AssertEqual(t, errResp.Error.Code, contract.JSONRPCInvalidParams)
	kilnError, ok := errResp.Error.Data["kiln_error"].(map[string]any)
	utest.AssertTrue(t, ok, "kiln_error should be object")
	code, ok := kilnError["code"].(string)
	utest.AssertTrue(t, ok, "kiln_error.code should be string")
	utest.AssertEqual(t, code, "runtime.invalid_params")
	utest.AssertNotNil(t, state.LastFatalStartupError, "fatal error should be stored in state")
}

// TestMakeShutdownHandler_InvalidParams tests that shutdown handler returns error for invalid params
func TestMakeShutdownHandler_InvalidParams(t *testing.T) {
	t.Parallel()

	state := &handler.HandlerState{}
	deps := &contract.RuntimeDeps{
		Lifecycle:       contract.NewLifecycle(),
		PendingRequests: protocol.NewPendingRequests(),
	}

	shutdownHandler := handler.MakeShutdownHandler(state, deps)
	requestID := int64(2)

	req := protocol.Request{
		JSONRPC: protocol.DefaultJSONRPCVersion,
		ID:      protocol.ID{Number: &requestID},
		Method:  "runtime.shutdown",
		Params:  map[string]any{},
	}

	resp := shutdownHandler(context.Background(), req)
	utest.AssertTrue(t, resp.IsErrorResponse(), "expected error response for invalid params")

	errResp := resp.(protocol.ErrorResponse)
	utest.AssertEqual(t, errResp.Error.Code, contract.JSONRPCInvalidParams)
	kilnError, ok := errResp.Error.Data["kiln_error"].(map[string]any)
	utest.AssertTrue(t, ok, "kiln_error should be object")
	code, ok := kilnError["code"].(string)
	utest.AssertTrue(t, ok, "kiln_error.code should be string")
	utest.AssertEqual(t, code, "runtime.invalid_params")
	utest.AssertNotNil(t, state.LastFatalStartupError, "fatal error should be stored in state")
}

// TestMakeShutdownHandler_AcceptsRequest tests shutdown handler when the runtime begins draining
func TestMakeShutdownHandler_AcceptsRequest(t *testing.T) {
	t.Parallel()

	state := &handler.HandlerState{}
	pendingRequests := protocol.NewPendingRequests()
	pendingRequests.Add("request-1", "repository.search")
	deps := &contract.RuntimeDeps{
		Lifecycle:       contract.NewLifecycle(),
		PendingRequests: pendingRequests,
	}

	shutdownHandler := handler.MakeShutdownHandler(state, deps)
	requestID := int64(3)

	req := protocol.Request{
		JSONRPC: protocol.DefaultJSONRPCVersion,
		ID:      protocol.ID{Number: &requestID},
		Method:  "runtime.shutdown",
		Params: map[string]any{
			"grace_period_seconds":      5,
			"cancel_in_flight_requests": true,
			"reason":                    "maintenance",
		},
	}

	resp := shutdownHandler(context.Background(), req)
	utest.AssertTrue(t, resp.IsSuccessResponse(), "shutdown should return success response")

	successResp := resp.(*protocol.SuccessResponse)
	result := successResp.Result

	acceptedVal, ok := result["accepted"].(bool)
	utest.AssertTrue(t, ok, "accepted should be bool")
	utest.AssertEqual(t, acceptedVal, true)

	drainingVal, ok := result["draining"].(bool)
	utest.AssertTrue(t, ok, "draining should be bool")
	utest.AssertEqual(t, drainingVal, true)

	shutdownVal, ok := result["shutdown"].(bool)
	utest.AssertTrue(t, ok, "shutdown should be bool")
	utest.AssertEqual(t, shutdownVal, false)

	countVal, ok := result["in_flight_request_count"].(float64)
	utest.AssertTrue(t, ok, "in_flight_request_count should be number")
	utest.AssertEqual(t, countVal, float64(1))
	utest.AssertEqual(t, state.Draining, true)
}

// TestMakeShutdownHandler_AlreadyDraining tests shutdown handler when the runtime is already draining
func TestMakeShutdownHandler_AlreadyDraining(t *testing.T) {
	t.Parallel()

	state := &handler.HandlerState{}
	state.Draining = true
	pendingRequests := protocol.NewPendingRequests()
	pendingRequests.Add("request-1", "repository.search")
	pendingRequests.Add("request-2", "repository.get_source")
	deps := &contract.RuntimeDeps{
		Lifecycle:       contract.NewLifecycle(),
		PendingRequests: pendingRequests,
	}

	shutdownHandler := handler.MakeShutdownHandler(state, deps)
	requestID := int64(4)

	req := protocol.Request{
		JSONRPC: protocol.DefaultJSONRPCVersion,
		ID:      protocol.ID{Number: &requestID},
		Method:  "runtime.shutdown",
		Params: map[string]any{
			"grace_period_seconds":      10,
			"cancel_in_flight_requests": false,
			"reason":                    "retry",
		},
	}

	resp := shutdownHandler(context.Background(), req)
	utest.AssertTrue(t, resp.IsSuccessResponse(), "shutdown should return success response")

	successResp := resp.(*protocol.SuccessResponse)
	result := successResp.Result

	acceptedVal, ok := result["accepted"].(bool)
	utest.AssertTrue(t, ok, "accepted should be bool")
	utest.AssertEqual(t, acceptedVal, false)

	drainingVal, ok := result["draining"].(bool)
	utest.AssertTrue(t, ok, "draining should be bool")
	utest.AssertEqual(t, drainingVal, true)

	shutdownVal, ok := result["shutdown"].(bool)
	utest.AssertTrue(t, ok, "shutdown should be bool")
	utest.AssertEqual(t, shutdownVal, false)

	countVal, ok := result["in_flight_request_count"].(float64)
	utest.AssertTrue(t, ok, "in_flight_request_count should be number")
	utest.AssertEqual(t, countVal, float64(2))
	utest.AssertEqual(t, state.Draining, true)
}

// TestMakeShutdownHandler_AlreadyShutdown tests shutdown handler when the runtime is already shut down
func TestMakeShutdownHandler_AlreadyShutdown(t *testing.T) {
	t.Parallel()

	state := &handler.HandlerState{}
	state.Shutdown = true
	deps := &contract.RuntimeDeps{
		Lifecycle:       contract.NewLifecycle(),
		PendingRequests: protocol.NewPendingRequests(),
	}

	shutdownHandler := handler.MakeShutdownHandler(state, deps)
	requestID := int64(5)

	req := protocol.Request{
		JSONRPC: protocol.DefaultJSONRPCVersion,
		ID:      protocol.ID{Number: &requestID},
		Method:  "runtime.shutdown",
		Params: map[string]any{
			"grace_period_seconds":      1,
			"cancel_in_flight_requests": true,
			"reason":                    "complete",
		},
	}

	resp := shutdownHandler(context.Background(), req)
	utest.AssertTrue(t, resp.IsSuccessResponse(), "shutdown should return success response")

	successResp := resp.(*protocol.SuccessResponse)
	result := successResp.Result

	acceptedVal, ok := result["accepted"].(bool)
	utest.AssertTrue(t, ok, "accepted should be bool")
	utest.AssertEqual(t, acceptedVal, false)

	drainingVal, ok := result["draining"].(bool)
	utest.AssertTrue(t, ok, "draining should be bool")
	utest.AssertEqual(t, drainingVal, false)

	shutdownVal, ok := result["shutdown"].(bool)
	utest.AssertTrue(t, ok, "shutdown should be bool")
	utest.AssertEqual(t, shutdownVal, true)

	countVal, ok := result["in_flight_request_count"].(float64)
	utest.AssertTrue(t, ok, "in_flight_request_count should be number")
	utest.AssertEqual(t, countVal, float64(0))
	utest.AssertEqual(t, state.Shutdown, true)
}

// TestMakeShutdownHandler_CompletesWithCancelInFlightRequests tests that shutdown worker cancels pending requests and marks runtime as shut down.
func TestMakeShutdownHandler_CompletesWithCancelInFlightRequests(t *testing.T) {
	t.Parallel()

	state := &handler.HandlerState{}
	pendingRequests := protocol.NewPendingRequests()
	pendingRequests.Add("request-1", "repository.search")
	pendingRequests.Add("request-2", "repository.get_source")
	deps := &contract.RuntimeDeps{
		Lifecycle:       contract.NewLifecycle(),
		PendingRequests: pendingRequests,
	}

	shutdownHandler := handler.MakeShutdownHandler(state, deps)
	requestID := int64(6)

	req := protocol.Request{
		JSONRPC: protocol.DefaultJSONRPCVersion,
		ID:      protocol.ID{Number: &requestID},
		Method:  "runtime.shutdown",
		Params: map[string]any{
			"grace_period_seconds":      1,
			"cancel_in_flight_requests": true,
			"reason":                    "maintenance",
		},
	}

	resp := shutdownHandler(context.Background(), req)
	utest.AssertTrue(t, resp.IsSuccessResponse(), "shutdown should return success response")

	waitForCondition(t, 4*time.Second, func() bool {
		state.Mu.Lock()
		defer state.Mu.Unlock()
		return state.Shutdown
	})

	utest.AssertEqual(t, pendingRequests.Count(), int64(0))
	state.Mu.Lock()
	utest.AssertEqual(t, state.Draining, true)
	utest.AssertEqual(t, state.Shutdown, true)
	state.Mu.Unlock()
}

// TestMakeShutdownHandler_CompletesAfterInFlightRequestsDrain tests that shutdown worker waits for in-flight requests and only then marks runtime as shut down.
func TestMakeShutdownHandler_CompletesAfterInFlightRequestsDrain(t *testing.T) {
	t.Parallel()

	state := &handler.HandlerState{}
	pendingRequests := protocol.NewPendingRequests()
	pendingRequests.Add("request-1", "repository.search")
	deps := &contract.RuntimeDeps{
		Lifecycle:       contract.NewLifecycle(),
		PendingRequests: pendingRequests,
	}

	shutdownHandler := handler.MakeShutdownHandler(state, deps)
	requestID := int64(7)

	req := protocol.Request{
		JSONRPC: protocol.DefaultJSONRPCVersion,
		ID:      protocol.ID{Number: &requestID},
		Method:  "runtime.shutdown",
		Params: map[string]any{
			"grace_period_seconds":      1,
			"cancel_in_flight_requests": false,
			"reason":                    "drain",
		},
	}

	resp := shutdownHandler(context.Background(), req)
	utest.AssertTrue(t, resp.IsSuccessResponse(), "shutdown should return success response")

	time.AfterFunc(50*time.Millisecond, func() {
		pendingRequests.Pop("request-1")
	})

	waitForCondition(t, 5*time.Second, func() bool {
		state.Mu.Lock()
		defer state.Mu.Unlock()
		return state.Shutdown
	})

	utest.AssertEqual(t, pendingRequests.Count(), int64(0))
	state.Mu.Lock()
	utest.AssertEqual(t, state.Draining, true)
	utest.AssertEqual(t, state.Shutdown, true)
	state.Mu.Unlock()
}

// TestMakeShutdownHandler_ContextCanceledDuringGracePeriod tests that canceling the request context stops shutdown before completion.
func TestMakeShutdownHandler_ContextCanceledDuringGracePeriod(t *testing.T) {
	t.Parallel()

	state := &handler.HandlerState{}
	pendingRequests := protocol.NewPendingRequests()
	pendingRequests.Add("request-1", "repository.search")
	deps := &contract.RuntimeDeps{
		Lifecycle:       contract.NewLifecycle(),
		PendingRequests: pendingRequests,
	}

	shutdownHandler := handler.MakeShutdownHandler(state, deps)
	requestID := int64(8)
	ctx, cancel := context.WithCancel(context.Background())

	req := protocol.Request{
		JSONRPC: protocol.DefaultJSONRPCVersion,
		ID:      protocol.ID{Number: &requestID},
		Method:  "runtime.shutdown",
		Params: map[string]any{
			"grace_period_seconds":      5,
			"cancel_in_flight_requests": false,
			"reason":                    "cancel-test",
		},
	}

	resp := shutdownHandler(ctx, req)
	utest.AssertTrue(t, resp.IsSuccessResponse(), "shutdown should return success response")

	cancel()
	time.Sleep(150 * time.Millisecond)

	state.Mu.Lock()
	utest.AssertEqual(t, state.Draining, true)
	utest.AssertEqual(t, state.Shutdown, false)
	state.Mu.Unlock()
	utest.AssertEqual(t, pendingRequests.Count(), int64(1))
}

// TestMakeShutdownHandler_ContextTimeoutWhileWaitingForInFlight tests that timeout while draining still completes shutdown state.
func TestMakeShutdownHandler_ContextTimeoutWhileWaitingForInFlight(t *testing.T) {
	t.Parallel()

	state := &handler.HandlerState{}
	pendingRequests := protocol.NewPendingRequests()
	pendingRequests.Add("request-1", "repository.search")
	deps := &contract.RuntimeDeps{
		Lifecycle:       contract.NewLifecycle(),
		PendingRequests: pendingRequests,
	}

	shutdownHandler := handler.MakeShutdownHandler(state, deps)
	requestID := int64(9)
	ctx, cancel := context.WithTimeout(context.Background(), 1500*time.Millisecond)
	defer cancel()

	req := protocol.Request{
		JSONRPC: protocol.DefaultJSONRPCVersion,
		ID:      protocol.ID{Number: &requestID},
		Method:  "runtime.shutdown",
		Params: map[string]any{
			"grace_period_seconds":      1,
			"cancel_in_flight_requests": false,
			"reason":                    "timeout-test",
		},
	}

	resp := shutdownHandler(ctx, req)
	utest.AssertTrue(t, resp.IsSuccessResponse(), "shutdown should return success response")

	waitForCondition(t, 5*time.Second, func() bool {
		state.Mu.Lock()
		defer state.Mu.Unlock()
		return state.Shutdown
	})

	utest.AssertEqual(t, pendingRequests.Count(), int64(1))
	state.Mu.Lock()
	utest.AssertEqual(t, state.Draining, true)
	utest.AssertEqual(t, state.Shutdown, true)
	state.Mu.Unlock()
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
