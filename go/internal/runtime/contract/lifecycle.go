package contract

import "sync"

var once sync.Once

// Lifecycle represents the lifecycle of the runtime, including shutdown and exit.
type Lifecycle struct {
	// ShutdownCh is a channel that is closed when the runtime is shutting down and exiting the main loop.
	ShutdownCh chan struct{}
	// Wg is a WaitGroup to track all active background goroutines.
	Wg sync.WaitGroup
}

func NewLifecycle() *Lifecycle {
	return &Lifecycle{
		ShutdownCh: make(chan struct{}),
	}
}

// SignalShutdown closes the ShutdownCh channel to signal that the
// runtime is shutting down and exiting the main loop.
func (l *Lifecycle) SignalShutdown() {
	once.Do(func() {
		close(l.ShutdownCh)
	})
}
