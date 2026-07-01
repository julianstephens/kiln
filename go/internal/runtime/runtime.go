package runtime

import (
	"context"
)

func Run(ctx context.Context, cfg Config) error {
	if cfg.Input == nil {
		return ErrInputStreamMissing
	}
	if cfg.Output == nil {
		return ErrOutputStreamMissing
	}

	// Later:
	// - open persistence
	// - register protocol handlers
	// - emit runtime.session_started
	// - enter request loop

	return nil
}
