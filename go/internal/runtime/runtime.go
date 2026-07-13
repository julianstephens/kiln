package runtime

import (
	"context"
	"errors"
	"fmt"

	"github.com/julianstephens/kiln/go/internal/logger"
	"github.com/julianstephens/kiln/go/internal/persistence"
	"github.com/julianstephens/kiln/go/internal/protocol"
	"github.com/julianstephens/kiln/go/internal/runtime/contract"
	"github.com/julianstephens/kiln/go/internal/runtime/handler"
	"github.com/julianstephens/kiln/go/internal/runtime/rpcerror"
	runtime_error "github.com/julianstephens/kiln/go/schema/runtime/error"
)

var controlMethods = map[string]struct{}{
	"runtime.initialize": {},
	"runtime.health":     {},
	"runtime.shutdown":   {},
}

func Run(ctx context.Context, cfg Config) (err error) {
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
	defer func() {
		err = errors.Join(err, logCloser.Close())
	}()

	build, buildErr := contract.NewBuildInfo()
	if buildErr != nil {
		err = &Error{
			Code:    "runtime.build_info_error",
			Message: fmt.Sprintf("Failed to retrieve build info: %v", buildErr),
		}
	}

	lifecycle := contract.NewLifecycle()
	state := &handler.HandlerState{}
	var store persistence.Store

	store, openErr := persistence.Open(ctx, cfg.DB)
	if openErr != nil {
		fatalErr := normalizePersistenceStartupError(openErr)
		appLogger.Error(
			"persistence bootstrap failed",
			"code", fatalErr.Code,
			"error", openErr,
		)
		state.SetReady(false)
		state.SetLastFatalStartupError(fatalErr)
	} else {
		defer func() {
			if closeErr := store.Close(); closeErr != nil {
				err = errors.Join(err, closeErr)
			}
		}()
	}

	deps := &contract.RuntimeDeps{
		Build:           *build,
		Lifecycle:       lifecycle,
		Logger:          appLogger.With("component", "runtime"),
		PendingRequests: protocol.NewPendingRequests(),
		Store:           store,
	}
	return serveProtocol(ctx, cfg, deps, state)
}

func serveProtocol(
	ctx context.Context,
	cfg Config,
	deps *contract.RuntimeDeps,
	state *handler.HandlerState,
) (err error) {
	deps.Logger.Debug("runtime starting",
		"build_version", deps.Build.Version,
		"build_commit", deps.Build.Commit,
		"build_date", deps.Build.Date,
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
	defer func() {
		if closeErr := peer.Close(); closeErr != nil {
			deps.Logger.Error("failed to close protocol peer", "error", closeErr.Error())
			err = closeErr
		}
	}()

	cancelCtx, cancel := context.WithCancel(ctx)
	defer cancel()

	inCh := peer.InChan()

RequestLoop:
	for {
		select {
		case <-deps.Lifecycle.ShutdownCh:
			if len(inCh) > 0 {
				deps.Logger.Debug("runtime shutdown signal received with buffered requests, draining before exit",
					"buffered_requests", len(inCh),
				)
				continue
			}
			deps.Logger.Debug("runtime shutdown signal received, exiting request loop")
			break RequestLoop
		case <-cancelCtx.Done():
			deps.Logger.Debug("runtime context canceled, exiting request loop")
			break RequestLoop
		case res, ok := <-inCh:
			if !ok {
				draining, shutdown := state.ShutdownStatus()
				if draining || shutdown {
					deps.Logger.Debug("runtime input channel closed due to shutdown, exiting request loop")
					break RequestLoop
				}
				if peerErr := peer.LastErr(); peerErr != nil {
					err = peerErr
					return
				}
				deps.Logger.Debug("runtime input channel closed, exiting request loop")
				break RequestLoop
			}
			if res.Err != nil {
				if errors.Is(res.Err, context.Canceled) {
					deps.Logger.Debug("runtime request loop canceled, exiting")
					break RequestLoop
				}

				var protocolErr *protocol.Error
				if errors.As(res.Err, &protocolErr) && protocolErr.Code == protocol.CodeRuntimeStreamClosed {
					draining, shutdown := state.ShutdownStatus()
					if draining || shutdown {
						deps.Logger.Debug("runtime input stream closed during shutdown, exiting request loop")
						break RequestLoop
					}
				}
				err = res.Err
				return
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

			draining, shutdown := state.ShutdownStatus()
			if msg == nil && (draining || shutdown) && protocolReq.Method != "runtime.shutdown" {
				deps.Logger.Debug("runtime is shutting down",
					"request", req.ToJSON(),
				)
				msg, _ = rpcerror.Shutdown(protocolReq.ID, protocolReq.Method)
			}

			if notReadyErr := requireReady(protocolReq.ID, protocolReq.Method, state); notReadyErr != nil {
				msg = notReadyErr
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
					msg = router.Dispatch(cancelCtx, protocolReq)
					deps.PendingRequests.Pop(idStr)
				}
			}

			deps.Logger.Debug("runtime response ready",
				"request_id", protocolReq.ID.JSONValue(),
				"response_type", fmt.Sprintf("%T", msg),
			)

			if peerErr := peer.Send(msg); peerErr != nil {
				err = peerErr
				return
			}
		}
	}

	deps.Logger.Debug("runtime loop exited, waiting for background workers")
	cancel()
	deps.Lifecycle.Wg.Wait()
	deps.Logger.Debug("all background workers finished, runtime exiting")

	return
}

func normalizePersistenceStartupError(err error) *runtime_error.ErrorKilnError {
	var persistenceErr *persistence.Error
	if errors.As(err, &persistenceErr) {
		return &runtime_error.ErrorKilnError{
			Code:      "persistence." + persistenceErr.Code,
			Category:  persistenceErr.Category,
			Retryable: false,
			Message:   persistenceErr.Message,
			Details:   persistenceErr.Details(),
		}
	}
	return &runtime_error.ErrorKilnError{
		Code:      "persistence.startup_failed",
		Category:  "persistence",
		Retryable: false,
		Message:   "Persistence startup failed.",
	}
}

func requireReady(id protocol.ID, method string, state *handler.HandlerState) *protocol.ErrorResponse {
	if _, allowed := controlMethods[method]; allowed {
		return nil
	}

	if state.IsReady() {
		return nil
	}

	if fatal := state.GetLastFatalStartupError(); fatal != nil {
		msg, _ := rpcerror.RuntimeNotReady(id, method, fatal)
		return &msg
	}

	msg, _ := rpcerror.RuntimeNotReady(id, method, nil)
	return &msg
}
