package handler

import (
	"sync"

	runtime_error "github.com/julianstephens/kiln/go/schema/runtime/error"
	"github.com/julianstephens/kiln/go/schema/runtime/initialize_request_payload"
	"github.com/julianstephens/kiln/go/schema/runtime/initialize_result"
)

// HandlerState holds the mutable state of the runtime, including initialization status and last fatal error.
type HandlerState struct {
	Mu sync.Mutex

	Initialized   bool
	InitialParams initialize_request_payload.InitializeRequestPayload
	InitialResult initialize_result.InitializeResult

	Ready    bool
	Draining bool
	Shutdown bool

	LastFatalStartupError *runtime_error.ErrorKilnError
}

func (hs *HandlerState) IsInitialized() bool {
	hs.Mu.Lock()
	defer hs.Mu.Unlock()
	return hs.Initialized
}

func (hs *HandlerState) SetInitialized(initialized bool) {
	hs.Mu.Lock()
	defer hs.Mu.Unlock()
	hs.Initialized = initialized
}

func (hs *HandlerState) IsReady() bool {
	hs.Mu.Lock()
	defer hs.Mu.Unlock()
	return hs.Ready
}

func (hs *HandlerState) SetReady(ready bool) {
	hs.Mu.Lock()
	defer hs.Mu.Unlock()
	hs.Ready = ready
}

func (hs *HandlerState) IsDraining() bool {
	hs.Mu.Lock()
	defer hs.Mu.Unlock()
	return hs.Draining
}

func (hs *HandlerState) SetDraining(draining bool) {
	hs.Mu.Lock()
	defer hs.Mu.Unlock()
	hs.Draining = draining
}

func (hs *HandlerState) IsShutdown() bool {
	hs.Mu.Lock()
	defer hs.Mu.Unlock()
	return hs.Shutdown
}

func (hs *HandlerState) SetShutdown(shutdown bool) {
	hs.Mu.Lock()
	defer hs.Mu.Unlock()
	hs.Shutdown = shutdown
}

func (hs *HandlerState) ShutdownStatus() (draining, shutdown bool) {
	hs.Mu.Lock()
	defer hs.Mu.Unlock()
	return hs.Draining, hs.Shutdown
}

func (hs *HandlerState) GetLastFatalStartupError() *runtime_error.ErrorKilnError {
	hs.Mu.Lock()
	defer hs.Mu.Unlock()
	return hs.LastFatalStartupError
}

func (hs *HandlerState) SetLastFatalStartupError(err *runtime_error.ErrorKilnError) {
	hs.Mu.Lock()
	defer hs.Mu.Unlock()
	hs.LastFatalStartupError = err
}

func (hs *HandlerState) GetInitialParams() initialize_request_payload.InitializeRequestPayload {
	hs.Mu.Lock()
	defer hs.Mu.Unlock()
	return hs.InitialParams
}

func (hs *HandlerState) SetInitialParams(params initialize_request_payload.InitializeRequestPayload) {
	hs.Mu.Lock()
	defer hs.Mu.Unlock()
	hs.InitialParams = params
}

func (hs *HandlerState) GetInitialResult() initialize_result.InitializeResult {
	hs.Mu.Lock()
	defer hs.Mu.Unlock()
	return hs.InitialResult
}

func (hs *HandlerState) SetInitialResult(result initialize_result.InitializeResult) {
	hs.Mu.Lock()
	defer hs.Mu.Unlock()
	hs.InitialResult = result
}
