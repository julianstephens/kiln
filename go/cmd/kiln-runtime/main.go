package main

import (
	"context"
	"fmt"
	"os"

	"github.com/julianstephens/kiln/go/internal/runtime"
)

func main() {
	ctx := context.Background()

	cfg := runtime.Config{
		Input:  os.Stdin,
		Output: os.Stdout,
		Error:  os.Stderr,
	}

	if err := runtime.Run(ctx, cfg); err != nil {
		fmt.Fprintf(os.Stderr, "kiln runtime failed: %v\n", err)
		os.Exit(1)
	}
}
