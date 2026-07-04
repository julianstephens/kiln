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
