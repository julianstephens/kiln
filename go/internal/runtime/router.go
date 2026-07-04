package runtime

import (
	"context"
	"sync"

	"github.com/julianstephens/kiln/go/internal/protocol"
	"github.com/julianstephens/kiln/go/internal/runtime/contract"
	"github.com/julianstephens/kiln/go/internal/runtime/rpcerror"
	"github.com/julianstephens/kiln/go/internal/util"
)

// Router manages method-to-handler routing with dependency injection.
type Router struct {
	mu       sync.RWMutex
	handlers map[string]contract.Handler
}

func NewRouter() *Router {
	return &Router{
		handlers: make(map[string]contract.Handler),
	}
}

// Register binds a handler to a specific method name in the router.
func (r *Router) Register(method string, handler contract.Handler) {
	r.mu.Lock()
	defer r.mu.Unlock()
	r.handlers[method] = handler
}

// Dispatch routes the incoming request to the appropriate handler based on the method name.
func (r *Router) Dispatch(ctx context.Context, req protocol.Request) protocol.Message {
	r.mu.RLock()
	handler, ok := r.handlers[req.Method]
	r.mu.RUnlock()

	if !ok {
		return rpcerror.MethodNotFound(req.ID, req.Method)
	}

	msg := handler(ctx, req)
	if msg == nil {
		return rpcerror.Internal(req.ID, util.Ptr(req.Method), "Handler returned nil response", map[string]any{
			"requested_method": req.Method,
			"request_params":   req.Params,
		})
	}

	return msg
}
