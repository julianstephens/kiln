package runtime

import "io"

type Config struct {
	Input  io.Reader
	Output io.Writer
	Error  io.Writer
}
