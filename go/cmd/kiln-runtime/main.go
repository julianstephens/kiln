package main

import (
	"context"
	"flag"
	"fmt"
	"os"

	"github.com/itzg/go-flagsfiller"
	"github.com/julianstephens/kiln/go/internal/logger"
	"github.com/julianstephens/kiln/go/internal/persistence"
	"github.com/julianstephens/kiln/go/internal/runtime"
)

type Config struct {
	Logging logger.LoggingConfig `json:"logging"`
	DB      persistence.Config   `json:"db"`
}

func main() {
	ctx := context.Background()

	var cliCfg Config
	filler := flagsfiller.New()

	if err := filler.Fill(flag.CommandLine, &cliCfg); err != nil {
		fmt.Fprintf(os.Stderr, "failed to parse command line flags: %v\n", err)
		os.Exit(1)
	}
	flag.Parse()

	cfg := runtime.Config{
		Input:  os.Stdin,
		Output: os.Stdout,
		Error:  os.Stderr,

		Logging: cliCfg.Logging,
		DB:      cliCfg.DB,
	}

	if err := runtime.Run(ctx, cfg); err != nil {
		fmt.Fprintf(os.Stderr, "kiln runtime failed: %v\n", err)
		os.Exit(1)
	}
}
