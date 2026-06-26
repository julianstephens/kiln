package runtime

import (
	"context"
	"fmt"
)

func Run(ctx context.Context, cfg Config) error {
	if cfg.Input == nil {
		return fmt.Errorf("runtime input is required")
	}
	if cfg.Output == nil {
		return fmt.Errorf("runtime output is required")
	}

	// Later:
	// - open persistence
	// - register protocol handlers
	// - emit runtime.session_started
	// - enter request loop

	return nil
}
