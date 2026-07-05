package runtime

import (
	"context"
	"errors"
	"fmt"

	"github.com/julianstephens/kiln/go/internal/logger"
	"github.com/julianstephens/kiln/go/internal/protocol"
	"github.com/julianstephens/kiln/go/internal/runtime/contract"
	"github.com/julianstephens/kiln/go/internal/runtime/handler"
	"github.com/julianstephens/kiln/go/internal/runtime/rpcerror"
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
	deps := &contract.RuntimeDeps{
		Build:           *build,
		Lifecycle:       contract.NewLifecycle(),
		Logger:          appLogger.With("component", "runtime"),
		PendingRequests: protocol.NewPendingRequests(),
	}
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
	router.Register("runtime.shutdown", handler.MakeShutdownHandler(state, deps))
	deps.Logger.Debug("runtime handlers registered",
		"handlers", []string{"runtime.initialize", "runtime.health", "runtime.shutdown"},
	)

	// - emit runtime.session_started
	// - enter request loop
	peer := protocol.NewPeer(cfg.Input, cfg.Output, protocol.DefaultMaxMessageBytes)
	cancelCtx, cancel := context.WithCancel(ctx)
	defer cancel()

RequestLoop:
	for {
		select {
		case <-deps.Lifecycle.ShutdownCh:
			deps.Logger.Debug("runtime shutdown signal received, exiting request loop")
			break RequestLoop
		case res := <-peer.ReceiveCh(cancelCtx):
			if res.Err != nil {
				if errors.Is(res.Err, context.Canceled) {
					deps.Logger.Debug("runtime request loop canceled, exiting")
					break RequestLoop
				}
				return res.Err
			}

			req := res.Msg
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
				msg, _ = rpcerror.ParseError(map[string]any{
					"request": req.ToJSON(),
				})
			}

			if msg == nil && protocolReq.ID.Null {
				deps.Logger.Debug("runtime request missing ID", "request", req.ToJSON())
				msg, _ = rpcerror.InvalidRequest(protocolReq.ID, protocolReq.Method, map[string]any{
					"request": req.ToJSON(),
				})
			}

			if msg == nil && (state.Draining || state.Shutdown) && protocolReq.Method != "runtime.shutdown" {
				deps.Logger.Debug("runtime is shutting down",
					"request", req.ToJSON(),
				)
				msg, _ = rpcerror.Shutdown(protocolReq.ID, protocolReq.Method)
			}

			if msg == nil {
				deps.Logger.Debug("dispatching runtime request",
					"method", protocolReq.Method,
					"id", protocolReq.ID.JSONValue(),
				)

				id := protocolReq.ID.JSONValue()
				idStr, ok := id.(string)
				if id == nil || !ok {
					deps.Logger.Debug("runtime request had invalid ID",
						"request", req.ToJSON(),
					)
					msg, _ = rpcerror.InvalidRequest(protocolReq.ID, protocolReq.Method, map[string]any{"request": req.ToJSON()})
				} else {

					deps.PendingRequests.Add(idStr, protocolReq.Method)
					defer deps.PendingRequests.Pop(idStr)
					msg = router.Dispatch(cancelCtx, protocolReq)
				}
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

	deps.Logger.Debug("runtime loop exited, waiting for background workers")
	deps.Lifecycle.Wg.Wait()
	deps.Logger.Debug("all background workers finished, runtime exiting")

	return nil
}
