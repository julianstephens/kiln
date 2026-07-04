package main

import (
	"context"
	"fmt"
	"os"

	"github.com/julianstephens/kiln/go/internal/logger"
	"github.com/julianstephens/kiln/go/internal/runtime"
)

func main() {
	ctx := context.Background()

	cfg := runtime.Config{
		Input:  os.Stdin,
		Output: os.Stdout,
		Error:  os.Stderr,

		Logging: logger.LoggingConfig{
			Level: "debug",
			Sink: logger.LogSinkConfig{
				Kind:      logger.LogSinkKindLocalFile,
				Directory: "./tmp/logs",
				Filename:  "runtime.log",
				MaxBytes:  10 * 1024 * 1024, // 10 MB
				MaxFiles:  5,
			},
		},
	}

	if err := runtime.Run(ctx, cfg); err != nil {
		fmt.Fprintf(os.Stderr, "kiln runtime failed: %v\n", err)
		os.Exit(1)
	}
}
