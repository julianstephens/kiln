package handler

import (
	"context"
	"fmt"
	"time"

	"github.com/julianstephens/kiln/go/internal/protocol"
	"github.com/julianstephens/kiln/go/internal/runtime/contract"
	"github.com/julianstephens/kiln/go/internal/runtime/rpcerror"
	"github.com/julianstephens/kiln/go/internal/util"
	"github.com/julianstephens/kiln/go/schema/runtime/shutdown_request_payload"
	"github.com/julianstephens/kiln/go/schema/runtime/shutdown_result"
)

const (
	// ShutdownTimeoutSeconds is the maximum time to wait for in-flight requests to complete before forcing shutdown.
	ShutdownTimeoutSeconds = 30
)

// MakeShutdownHandler returns a Handler closure that captures state and deps.
func MakeShutdownHandler(state *HandlerState, deps *contract.RuntimeDeps) contract.Handler {
	return func(ctx context.Context, req protocol.Request) protocol.Message {
		state.Mu.Lock()
		defer state.Mu.Unlock()

		if deps != nil && deps.Logger != nil {
			deps.Logger.Debug("shutdown request received",
				"request_id", req.ID.JSONValue(),
				"params", req.Params,
			)
		}

		if state.Draining {
			if deps != nil && deps.Logger != nil {
				deps.Logger.Debug("shutdown request ignored, already draining",
					"request_id", req.ID.JSONValue(),
				)
			}
			return protocol.NewSuccessResponse(req.ID, util.MustStructToMap(shutdown_result.ShutdownResult{
				Accepted:             false,
				Draining:             true,
				Shutdown:             false,
				InFlightRequestCount: int(deps.PendingRequests.Count()),
			}))
		}

		if state.Shutdown {
			if deps != nil && deps.Logger != nil {
				deps.Logger.Debug("shutdown request ignored, already shut down",
					"request_id", req.ID.JSONValue(),
				)
			}
			return protocol.NewSuccessResponse(req.ID, util.MustStructToMap(shutdown_result.ShutdownResult{
				Accepted:             false,
				Draining:             false,
				Shutdown:             true,
				InFlightRequestCount: 0,
			}))
		}

		shutdownMethod := protocol.KilnMethods["runtime.shutdown"]
		res, err := shutdownMethod.ValidateParams(req.Params)
		if err != nil {
			if deps != nil && deps.Logger != nil {
				deps.Logger.Debug("shutdown request validation failed",
					"request_id", req.ID.JSONValue(),
					"params", req.Params,
					"error", err.Error(),
				)
			}
			errRes, kilnErr := rpcerror.InvalidParams(req.ID, req.Method, map[string]any{
				"params": req.Params,
			})
			state.LastFatalStartupError = &kilnErr
			return errRes
		}

		validatedParams, ok := res.(*shutdown_request_payload.ShutdownRequestPayload)
		if !ok {
			if deps != nil && deps.Logger != nil {
				deps.Logger.Debug("shutdown request validation returned unexpected type",
					"request_id", req.ID.JSONValue(),
					"params", req.Params,
					"validated_type", fmt.Sprintf("%T", res),
				)
			}
			errRes, kilnErr := rpcerror.Internal(
				req.ID,
				&req.Method,
				"initialize params validator returned unexpected type",
				map[string]any{
					"params":         req.Params,
					"validated_type": fmt.Sprintf("%T", res),
				},
			)
			state.LastFatalStartupError = &kilnErr
			return errRes
		}

		if deps != nil && deps.Logger != nil {
			deps.Logger.Debug("shutdown request validated",
				"request_id", req.ID.JSONValue(),
				"cancel_in_flight_requests", validatedParams.CancelInFlightRequests,
				"reason", validatedParams.Reason,
			)
		}

		if deps != nil && deps.Logger != nil {
			deps.Logger.Debug("shutdown request processing",
				"request_id", req.ID.JSONValue(),
				"cancel_in_flight_requests", validatedParams.CancelInFlightRequests,
				"reason", validatedParams.Reason,
			)
		}

		state.Draining = true
		startShutdownWorker(
			ctx,
			state,
			deps,
			validatedParams.CancelInFlightRequests,
		)

		return protocol.NewSuccessResponse(req.ID, util.MustStructToMap(shutdown_result.ShutdownResult{
			Accepted:             true,
			Draining:             true,
			Shutdown:             false,
			InFlightRequestCount: int(deps.PendingRequests.Count()),
		}))
	}
}

// startShutdownWorker starts a goroutine that handles the shutdown process, including canceling in-flight requests if specified.
// It updates the HandlerState to indicate that the shutdown process has started and completed.
func startShutdownWorker(
	ctx context.Context,
	state *HandlerState,
	deps *contract.RuntimeDeps,
	cancelInFlightRequests bool,
) {
	deps.Lifecycle.Wg.Go(func() {
		if deps != nil && deps.Logger != nil {
			deps.Logger.Debug("shutdown worker started")
		}

		cancelCtx, cancel := context.WithTimeout(ctx, ShutdownTimeoutSeconds*time.Second)
		defer cancel()

		doShutdown(cancelCtx, deps, cancelInFlightRequests)

		if deps != nil && deps.Logger != nil {
			deps.Logger.Debug("shutdown worker completed, setting state.Shutdown to true")
		}

		// signal the main loop to exit
		close(deps.Lifecycle.ShutdownCh)

		state.Mu.Lock()
		defer state.Mu.Unlock()
		state.Shutdown = true
	})
}

// doShutdown performs the actual shutdown logic, including canceling in-flight requests if specified.
func doShutdown(ctx context.Context, deps *contract.RuntimeDeps, cancelInFlightRequests bool) {
	if cancelInFlightRequests {
		if deps != nil && deps.Logger != nil {
			deps.Logger.Debug("shutdown worker canceling all in-flight requests")
		}
		deps.PendingRequests.CancelAll()
	} else {
		if deps != nil && deps.Logger != nil {
			deps.Logger.Debug("shutdown worker waiting for in-flight requests to complete")
		}
		// Wait for in-flight requests to complete or context to be done
		for {
			if deps.PendingRequests.Count() == 0 {
				if deps != nil && deps.Logger != nil {
					deps.Logger.Debug("shutdown worker all in-flight requests completed")
				}
				break
			}
			select {
			case <-ctx.Done():
				if deps != nil && deps.Logger != nil {
					deps.Logger.Debug(
						"shutdown worker context canceled while waiting for in-flight requests to complete",
					)
				}
				return
			case <-time.After(1 * time.Second):
				if deps != nil && deps.Logger != nil {
					deps.Logger.Debug("shutdown worker still waiting for in-flight requests to complete",
						"in_flight_request_count", deps.PendingRequests.Count(),
					)
				}
			}
		}
	}

	// later we can add more shutdown logic here, such as closing connections, cleaning up resources, etc.
}
