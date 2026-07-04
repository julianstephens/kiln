package runtime

import (
	"io"

	"github.com/julianstephens/kiln/go/internal/logger"
)

type Config struct {
	Input  io.Reader
	Output io.Writer
	Error  io.Writer

	Logging logger.LoggingConfig
}
