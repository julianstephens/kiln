package runtime

import (
	"context"
	"fmt"

	"github.com/julianstephens/kiln/go/internal/logger"
	"github.com/julianstephens/kiln/go/internal/protocol"
	"github.com/julianstephens/kiln/go/internal/runtime/contract"
	"github.com/julianstephens/kiln/go/internal/runtime/handler"
	"github.com/julianstephens/kiln/go/internal/util"
	runtime_error "github.com/julianstephens/kiln/go/schema/runtime/error"
)

func Run(ctx context.Context, cfg Config) error {
	if cfg.Input == nil {
		return ErrInputStreamMissing
	}
	if cfg.Output == nil {
		return ErrOutputStreamMissing
	}

	appLogger, logCloser, err := logger.NewLogger(cfg.Logging, cfg.Error)
	if err != nil {
		return &Error{
			Code:    CodeLogSinkOpenFailed,
			Message: "failed to open log sink",
			Details: err.Error(),
		}
	}

	build, err := contract.NewBuildInfo()
	if err != nil {
		_ = logCloser.Close()
		return &Error{
			Code:    "runtime.build_info_error",
			Message: fmt.Sprintf("Failed to retrieve build info: %v", err),
		}
	}
	defer func() {
		_ = logCloser.Close()
	}()
	// Later: - open persistence
	deps := &contract.RuntimeDeps{Build: *build, Logger: appLogger.With("component", "runtime")}
	state := &handler.HandlerState{}
	deps.Logger.Debug("runtime starting",
		"build_version", build.Version,
		"build_commit", build.Commit,
		"build_date", build.Date,
	)

	// - register protocol handlers
	router := NewRouter()
	router.Register("runtime.initialize", handler.MakeInitializeHandler(state, deps))
	router.Register("runtime.health", handler.MakeHealthHandler(state))
	deps.Logger.Debug("runtime handlers registered",
		"handlers", []string{"runtime.initialize", "runtime.health"},
	)

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

		deps.Logger.Debug("runtime request received", "request", req.ToJSON())

		var msg protocol.Message
		protocolReq, ok := req.(protocol.Request)
		if !ok {
			deps.Logger.Debug("runtime request had unexpected type",
				"request", req.ToJSON(),
			)
			inner := runtime_error.ErrorKilnError{
				Code:     "runtime.invalid_request_format",
				Category: "validation",
				Message:  "Request is not a valid JSON-RPC request object",
				Details: map[string]any{
					"request": req.ToJSON(),
				},
			}
			msg = protocol.NewErrorResponse(protocol.ID{Null: true}, protocol.ErrorObject{
				Code:    contract.JSONRPCInvalidRequest,
				Message: "Invalid request format",
				Data: util.MustStructToMap(runtime_error.Error{
					KilnError: inner,
				}),
			})
		}

		if msg == nil {
			deps.Logger.Debug("dispatching runtime request",
				"method", protocolReq.Method,
				"id", protocolReq.ID.JSONValue(),
			)
			msg = router.Dispatch(cancelCtx, protocolReq)
		}

		deps.Logger.Debug("runtime response ready",
			"request_id", protocolReq.ID.JSONValue(),
			"response_type", fmt.Sprintf("%T", msg),
		)

		if err := peer.Send(msg); err != nil {
			return err
		}
	}
}
