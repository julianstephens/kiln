package logger

import (
	"fmt"
	"io"
	"log/slog"
)

type LoggingConfig struct {
	Level string        `json:"level"`
	Sink  LogSinkConfig `json:"log_sink"`
}

func NewLogger(cfg LoggingConfig, fallback io.Writer) (*slog.Logger, io.Closer, error) {
	sink, err := OpenLogSink(cfg.Sink, fallback)
	if err != nil {
		return nil, nil, err
	}

	var level slog.Level
	switch cfg.Level {
	case "debug":
		level = slog.LevelDebug
	case "info", "":
		level = slog.LevelInfo
	case "warn":
		level = slog.LevelWarn
	case "error":
		level = slog.LevelError
	default:
		_ = sink.Close()
		return nil, nil, fmt.Errorf("unsupported log level: %q", cfg.Level)
	}

	handler := slog.NewJSONHandler(sink, &slog.HandlerOptions{
		Level: level,
	})

	return slog.New(handler), sink, nil
}
