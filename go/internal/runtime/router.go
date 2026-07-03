package runtime

import (
	"context"
	"sync"

	"github.com/julianstephens/kiln/go/internal/protocol"
	"github.com/julianstephens/kiln/go/internal/runtime/contract"
	runtime_error "github.com/julianstephens/kiln/go/schema/runtime/error"
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
		return protocol.NewErrorResponse(req.ID, protocol.ErrorObject{
			Code:    contract.JSONRPCMethodNotFound,
			Message: "Method not found",
			Data: runtime_error.Error{
				KilnError: runtime_error.ErrorKilnError{
					Code:     "runtime.method_not_found",
					Category: "compatibility",
					Message:  "Method not found",
					Details: map[string]any{
						"requested_method": req.Method,
					},
				},
			},
		})
	}

	msg := handler(ctx, req)
	if msg == nil {
		return protocol.NewErrorResponse(req.ID, protocol.ErrorObject{
			Code:    contract.JSONRPCInternalError,
			Message: "Handler returned nil",
			Data: runtime_error.Error{
				KilnError: runtime_error.ErrorKilnError{
					Code:     "runtime.internal_error",
					Category: "internal",
					Message:  "Handler returned nil response",
					Details: map[string]any{
						"requested_method": req.Method,
						"request_params":   req.Params,
					},
				},
			},
		})
	}

	return msg
}
