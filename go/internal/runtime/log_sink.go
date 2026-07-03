package runtime

import (
	"compress/gzip"
	"errors"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"sync"
)

type LogSinkKind string

const (
	LogSinkKindStderr    LogSinkKind = "stderr"
	LogSinkKindLocalFile LogSinkKind = "local_file"
)

type LogSinkConfig struct {
	Kind LogSinkKind `json:"kind"`

	Directory string `json:"directory,omitempty"`
	Filename  string `json:"filename,omitempty"`

	MaxBytes int64 `json:"max_bytes,omitempty"`
	MaxFiles int   `json:"max_files,omitempty"`
	Compress bool  `json:"compress,omitempty"`
}

type nopWriteCloser struct {
	io.Writer
}

func (w nopWriteCloser) Close() error {
	return nil
}

func OpenLogSink(cfg LogSinkConfig, fallback io.Writer) (io.WriteCloser, error) {
	switch cfg.Kind {
	case "", LogSinkKindStderr:
		if fallback == nil {
			fallback = io.Discard
		}
		return nopWriteCloser{Writer: fallback}, nil
	case LogSinkKindLocalFile:
		return newRotatingFileLogSink(cfg)
	default:
		return nil, fmt.Errorf("unsupported log sink kind: %q", cfg.Kind)
	}
}

type rotatingFileLogSink struct {
	cfg  LogSinkConfig
	mu   sync.Mutex
	file *os.File
	size int64
}

func newRotatingFileLogSink(cfg LogSinkConfig) (*rotatingFileLogSink, error) {
	if err := validateLocalFileLogSink(cfg); err != nil {
		return nil, err
	}
	if err := os.MkdirAll(cfg.Directory, 0o700); err != nil {
		return nil, fmt.Errorf("create log directory: %w", err)
	}

	sink := &rotatingFileLogSink{cfg: cfg}
	if err := sink.openLocked(); err != nil {
		return nil, err
	}
	return sink, nil
}

func validateLocalFileLogSink(cfg LogSinkConfig) error {
	if cfg.Directory == "" {
		return errors.New("local file log sink requires directory")
	}
	if cfg.Filename == "" {
		return errors.New("local file log sink requires filename")
	}
	if cfg.Filename != filepath.Base(cfg.Filename) {
		return errors.New("local file log sink filename must not include path separators")
	}
	if cfg.MaxBytes <= 0 {
		return errors.New("local file log sink requires max_bytes greater than zero")
	}
	if cfg.MaxFiles <= 0 {
		return errors.New("local file log sink requires max_files greater than zero")
	}
	return nil
}

func (s *rotatingFileLogSink) Write(p []byte) (int, error) {
	s.mu.Lock()
	defer s.mu.Unlock()

	if s.file == nil {
		if err := s.openLocked(); err != nil {
			return 0, err
		}
	}

	if s.size > 0 && s.size+int64(len(p)) > s.cfg.MaxBytes {
		if err := s.rotateLocked(); err != nil {
			return 0, err
		}
		if err := s.openLocked(); err != nil {
			return 0, err
		}
	}

	n, err := s.file.Write(p)
	s.size += int64(n)
	return n, err
}

func (s *rotatingFileLogSink) Close() error {
	s.mu.Lock()
	defer s.mu.Unlock()

	if s.file == nil {
		return nil
	}
	err := s.file.Close()
	s.file = nil
	s.size = 0
	return err
}

func (s *rotatingFileLogSink) openLocked() error {
	path := s.activePath()
	if info, err := os.Stat(path); err == nil && info.Size() >= s.cfg.MaxBytes {
		if err := s.rotateLocked(); err != nil {
			return err
		}
	} else if err != nil && !errors.Is(err, os.ErrNotExist) {
		return fmt.Errorf("stat active log file: %w", err)
	}

	file, err := os.OpenFile(path, os.O_CREATE|os.O_APPEND|os.O_WRONLY, 0o600)
	if err != nil {
		return fmt.Errorf("open active log file: %w", err)
	}

	info, err := file.Stat()
	if err != nil {
		closeErr := file.Close()
		if closeErr != nil {
			return fmt.Errorf("stat active log file: %w; close active log file: %w", err, closeErr)
		}
		return fmt.Errorf("stat active log file: %w", err)
	}

	s.file = file
	s.size = info.Size()
	return nil
}

func (s *rotatingFileLogSink) rotateLocked() error {
	if s.file != nil {
		if err := s.file.Close(); err != nil {
			return fmt.Errorf("close active log file before rotation: %w", err)
		}
		s.file = nil
		s.size = 0
	}

	if err := s.shiftRotatedLocked(); err != nil {
		return err
	}

	active := s.activePath()
	if _, err := os.Stat(active); errors.Is(err, os.ErrNotExist) {
		return nil
	} else if err != nil {
		return fmt.Errorf("stat active log file before rotation: %w", err)
	}

	rotated := s.rotatedPath(1)
	if s.cfg.Compress {
		if err := gzipFile(active, rotated); err != nil {
			return err
		}
		if err := os.Remove(active); err != nil {
			return fmt.Errorf("remove compressed active log file: %w", err)
		}
		return nil
	}

	if err := os.Rename(active, rotated); err != nil {
		return fmt.Errorf("rotate active log file: %w", err)
	}
	return nil
}

func (s *rotatingFileLogSink) shiftRotatedLocked() error {
	oldest := s.rotatedPath(s.cfg.MaxFiles)
	if err := os.Remove(oldest); err != nil && !errors.Is(err, os.ErrNotExist) {
		return fmt.Errorf("remove oldest rotated log file: %w", err)
	}

	for i := s.cfg.MaxFiles - 1; i >= 1; i-- {
		src := s.rotatedPath(i)
		dst := s.rotatedPath(i + 1)
		if _, err := os.Stat(src); errors.Is(err, os.ErrNotExist) {
			continue
		} else if err != nil {
			return fmt.Errorf("stat rotated log file: %w", err)
		}
		if err := os.Rename(src, dst); err != nil {
			return fmt.Errorf("shift rotated log file: %w", err)
		}
	}
	return nil
}

func (s *rotatingFileLogSink) activePath() string {
	return filepath.Join(s.cfg.Directory, s.cfg.Filename)
}

func (s *rotatingFileLogSink) rotatedPath(index int) string {
	name := fmt.Sprintf("%s.%d", s.cfg.Filename, index)
	if s.cfg.Compress {
		name += ".gz"
	}
	return filepath.Join(s.cfg.Directory, name)
}

func gzipFile(src string, dst string) error {
	in, err := os.Open(src)
	if err != nil {
		return fmt.Errorf("open log file for compression: %w", err)
	}

	out, err := os.OpenFile(dst, os.O_CREATE|os.O_TRUNC|os.O_WRONLY, 0o600)
	if err != nil {
		if closeErr := in.Close(); closeErr != nil {
			return fmt.Errorf("open compressed log file: %w; close source log file: %w", err, closeErr)
		}
		return fmt.Errorf("open compressed log file: %w", err)
	}

	zw := gzip.NewWriter(out)
	if _, err := io.Copy(zw, in); err != nil {
		closeGzipErr := zw.Close()
		closeOutErr := out.Close()
		closeInErr := in.Close()
		if closeGzipErr != nil {
			return fmt.Errorf("compress log file: %w; close gzip writer: %w", err, closeGzipErr)
		}
		if closeOutErr != nil {
			return fmt.Errorf("compress log file: %w; close compressed log file: %w", err, closeOutErr)
		}
		if closeInErr != nil {
			return fmt.Errorf("compress log file: %w; close source log file: %w", err, closeInErr)
		}
		return fmt.Errorf("compress log file: %w", err)
	}
	if err := zw.Close(); err != nil {
		closeOutErr := out.Close()
		closeInErr := in.Close()
		if closeOutErr != nil {
			return fmt.Errorf("close gzip writer: %w; close compressed log file: %w", err, closeOutErr)
		}
		if closeInErr != nil {
			return fmt.Errorf("close gzip writer: %w; close source log file: %w", err, closeInErr)
		}
		return fmt.Errorf("close gzip writer: %w", err)
	}
	if err := out.Close(); err != nil {
		closeInErr := in.Close()
		if closeInErr != nil {
			return fmt.Errorf("close compressed log file: %w; close source log file: %w", err, closeInErr)
		}
		return fmt.Errorf("close compressed log file: %w", err)
	}
	if err := in.Close(); err != nil {
		return fmt.Errorf("close source log file: %w", err)
	}
	return nil
}
