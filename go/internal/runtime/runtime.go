package runtime

import (
	"context"
	"fmt"

	"github.com/julianstephens/kiln/go/internal/protocol"
	"github.com/julianstephens/kiln/go/internal/runtime/contract"
	"github.com/julianstephens/kiln/go/internal/runtime/handler"
	runtime_error "github.com/julianstephens/kiln/go/schema/runtime/error"
)

func Run(ctx context.Context, cfg Config) error {
	if cfg.Input == nil {
		return ErrInputStreamMissing
	}
	if cfg.Output == nil {
		return ErrOutputStreamMissing
	}

	build, err := contract.NewBuildInfo()
	if err != nil {
		return &Error{
			Code:    "runtime.build_info_error",
			Message: fmt.Sprintf("Failed to retrieve build info: %v", err),
		}
	}
	// Later: - open persistence
	deps := &contract.RuntimeDeps{Build: *build}
	state := &handler.HandlerState{}

	// - register protocol handlers
	router := NewRouter()
	router.Register("runtime.initialize", handler.MakeInitializeHandler(state, deps))
	router.Register("runtime.health", handler.MakeHealthHandler(state))

	// - emit runtime.session_started
	// - enter request loop
	peer := protocol.NewPeer(cfg.Input, cfg.Output, protocol.DefaultMaxMessageBytes)
	cancelCtx, cancel := context.WithCancel(ctx)
	defer cancel()

	for {
		req, err := peer.Receive(cancelCtx)
		if err != nil {
			return err
		}
		if req == nil {
			continue
		}
		if !req.IsRequest() {
			continue
		}

		var msg protocol.Message
		protocolReq, ok := req.(protocol.Request)
		if !ok {
			msg = protocol.NewErrorResponse(protocol.ID{Null: true}, protocol.ErrorObject{
				Code:    contract.JSONRPCInvalidRequest,
				Message: "Invalid request format",
				Data: runtime_error.ErrorKilnError{
					Code:     "runtime.invalid_request_format",
					Category: "validation",
					Message:  "Request is not a valid JSON-RPC request object",
					Details: map[string]any{
						"request": req.ToJSON(),
					},
				},
			})
		}

		if msg == nil {
			msg = router.Dispatch(cancelCtx, protocolReq)
		}

		if err := peer.Send(msg); err != nil {
			return err
		}
	}
}
