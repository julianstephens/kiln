package handler

import (
	"sync"

	runtime_error "github.com/julianstephens/kiln/go/schema/runtime/error"
	"github.com/julianstephens/kiln/go/schema/runtime/initialize_request_payload"
	"github.com/julianstephens/kiln/go/schema/runtime/initialize_result"
)

// HandlerState holds the mutable state of the runtime, including initialization status and last fatal error.
type HandlerState struct {
	mu sync.Mutex

	initialized   bool
	initialParams initialize_request_payload.InitializeRequestPayload
	initialResult initialize_result.InitializeResult

	ready    bool
	draining bool
	shutdown bool

	lastFatalStartupError *runtime_error.ErrorKilnError
}
