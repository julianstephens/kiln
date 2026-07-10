package runtime

import (
	"io"

	"github.com/julianstephens/kiln/go/internal/logger"
	"github.com/julianstephens/kiln/go/internal/persistence"
)

type Config struct {
	Input  io.Reader
	Output io.Writer
	Error  io.Writer

	Logging logger.LoggingConfig
	DB      persistence.Config
}
