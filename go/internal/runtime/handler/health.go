package handler

import (
	"context"

	"github.com/julianstephens/kiln/go/internal/protocol"
	"github.com/julianstephens/kiln/go/internal/runtime/contract"
	"github.com/julianstephens/kiln/go/internal/runtime/rpcerror"
	"github.com/julianstephens/kiln/go/internal/util"
	"github.com/julianstephens/kiln/go/schema/runtime/health_result"
)

// MakeHealthHandler creates a handler for the health endpoint. It returns a function that takes a context and a request,
// and returns a response containing the current health status of the runtime.
func MakeHealthHandler(state *HandlerState) contract.Handler {
	return func(ctx context.Context, req protocol.Request) protocol.Message {
		state.Mu.Lock()
		isReady := state.Ready
		isShutdown := state.Shutdown
		isDraining := state.Draining
		isInitialized := state.Initialized
		lastFatalError := state.LastFatalStartupError
		state.Mu.Unlock()

		if req.Params != nil {
			err, _ := rpcerror.InvalidParams(req.ID, req.Method, map[string]any{
				"reason": "runtime.health does not accept parameters",
			})
			return err
		}

		return protocol.NewSuccessResponse(req.ID, util.MustStructToMap(health_result.HealthResult{
			Draining:              isDraining,
			Initialized:           isInitialized,
			LastFatalStartupError: lastFatalError,
			Ready:                 isReady,
			Shutdown:              isShutdown,
		}))
	}
}
