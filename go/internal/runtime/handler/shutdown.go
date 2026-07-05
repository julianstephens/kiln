package handler

import (
	"context"
	"fmt"

	"github.com/julianstephens/kiln/go/internal/protocol"
	"github.com/julianstephens/kiln/go/internal/runtime/contract"
	"github.com/julianstephens/kiln/go/internal/runtime/rpcerror"
	"github.com/julianstephens/kiln/go/internal/util"
	"github.com/julianstephens/kiln/go/schema/runtime/shutdown_request_payload"
	"github.com/julianstephens/kiln/go/schema/runtime/shutdown_result"
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
				"grace_period_seconds", validatedParams.GracePeriodSeconds,
				"reason", validatedParams.Reason,
			)
		}

		if state.Draining {
			return protocol.NewSuccessResponse(req.ID, util.MustStructToMap(shutdown_result.ShutdownResult{
				Accepted:             false,
				Draining:             true,
				Shutdown:             false,
				InFlightRequestCount: int(deps.PendingRequests.Count()),
			}))
		}

		if state.Shutdown {
			return protocol.NewSuccessResponse(req.ID, util.MustStructToMap(shutdown_result.ShutdownResult{
				Accepted:             false,
				Draining:             false,
				Shutdown:             true,
				InFlightRequestCount: 0,
			}))
		}

		state.Draining = true
		return protocol.NewSuccessResponse(req.ID, util.MustStructToMap(shutdown_result.ShutdownResult{
			Accepted:             true,
			Draining:             true,
			Shutdown:             false,
			InFlightRequestCount: int(deps.PendingRequests.Count()),
		}))
	}
}
