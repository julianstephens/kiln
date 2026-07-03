package handler

import (
	"context"

	"github.com/julianstephens/kiln/go/internal/protocol"
	"github.com/julianstephens/kiln/go/internal/runtime/contract"
	"github.com/julianstephens/kiln/go/internal/util"
	"github.com/julianstephens/kiln/go/schema/runtime/health_result"
)

// MakeHealthHandler creates a handler for the health endpoint. It returns a function that takes a context and a request,
// and returns a response containing the current health status of the runtime.
func MakeHealthHandler(state *HandlerState) contract.Handler {
	return func(ctx context.Context, req protocol.Request) protocol.Message {
		state.mu.Lock()
		isReady := state.ready
		isShutdown := state.shutdown
		isDraining := state.draining
		isInitialized := state.initialized
		lastFatalError := state.lastFatalStartupError
		state.mu.Unlock()

		return protocol.NewSuccessResponse(req.ID, util.StructToMap(health_result.HealthResult{
			Draining:              isDraining,
			Initialized:           isInitialized,
			LastFatalStartupError: lastFatalError,
			Ready:                 isReady,
			Shutdown:              isShutdown,
		}))
	}
}
