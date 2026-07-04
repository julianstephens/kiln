package logger_test

import (
	"bytes"
	"compress/gzip"
	"io"
	"os"
	"path/filepath"
	"testing"

	utest "github.com/julianstephens/go-utils/tests"

	"github.com/julianstephens/kiln/go/internal/logger"
)

func TestOpenLogSink_StderrUsesFallbackWriter(t *testing.T) {
	t.Parallel()

	var buf bytes.Buffer
	sink, err := logger.OpenLogSink(logger.LogSinkConfig{Kind: logger.LogSinkKindStderr}, &buf)
	utest.AssertNil(t, err)
	defer func() {
		_ = sink.Close()
	}()

	_, err = io.WriteString(sink, "hello\n")
	utest.AssertNil(t, err)
	utest.AssertEqual(t, buf.String(), "hello\n")
}

func TestOpenLogSink_EmptyKindUsesFallbackWriter(t *testing.T) {
	t.Parallel()

	var buf bytes.Buffer
	sink, err := logger.OpenLogSink(logger.LogSinkConfig{}, &buf)
	utest.AssertNil(t, err)
	defer func() {
		_ = sink.Close()
	}()

	_, err = io.WriteString(sink, "hello\n")
	utest.AssertNil(t, err)
	utest.AssertEqual(t, buf.String(), "hello\n")
}

func TestOpenLogSink_LocalFileWritesActiveLogFile(t *testing.T) {
	t.Parallel()

	dir := t.TempDir()
	sink, err := logger.OpenLogSink(logger.LogSinkConfig{
		Kind:      logger.LogSinkKindLocalFile,
		Directory: dir,
		Filename:  "logger.log",
		MaxBytes:  1024,
		MaxFiles:  3,
	}, nil)
	utest.AssertNil(t, err)
	defer func() {
		_ = sink.Close()
	}()

	_, err = io.WriteString(sink, "first\n")
	utest.AssertNil(t, err)

	// #nosec G304 -- test fixture path is derived from t.TempDir()
	content, err := os.ReadFile(filepath.Join(dir, "logger.log"))
	utest.AssertNil(t, err)
	utest.AssertEqual(t, string(content), "first\n")
}

func TestOpenLogSink_LocalFileRotatesWhenNextWriteWouldExceedLimit(t *testing.T) {
	t.Parallel()

	dir := t.TempDir()
	sink, err := logger.OpenLogSink(logger.LogSinkConfig{
		Kind:      logger.LogSinkKindLocalFile,
		Directory: dir,
		Filename:  "logger.log",
		MaxBytes:  6,
		MaxFiles:  2,
	}, nil)
	utest.AssertNil(t, err)
	defer func() {
		_ = sink.Close()
	}()

	_, err = io.WriteString(sink, "first\n")
	utest.AssertNil(t, err)
	_, err = io.WriteString(sink, "second\n")
	utest.AssertNil(t, err)

	// #nosec G304 -- test fixture path is derived from t.TempDir()
	active, err := os.ReadFile(filepath.Join(dir, "logger.log"))
	utest.AssertNil(t, err)
	utest.AssertEqual(t, string(active), "second\n")

	// #nosec G304 -- test fixture path is derived from t.TempDir()
	rotated, err := os.ReadFile(filepath.Join(dir, "logger.log.1"))
	utest.AssertNil(t, err)
	utest.AssertEqual(t, string(rotated), "first\n")
}

func TestOpenLogSink_LocalFileRemovesOldestRotatedFile(t *testing.T) {
	t.Parallel()

	dir := t.TempDir()
	sink, err := logger.OpenLogSink(logger.LogSinkConfig{
		Kind:      logger.LogSinkKindLocalFile,
		Directory: dir,
		Filename:  "logger.log",
		MaxBytes:  2,
		MaxFiles:  2,
	}, nil)
	utest.AssertNil(t, err)
	defer func() {
		_ = sink.Close()
	}()

	for _, line := range []string{"a\n", "b\n", "c\n", "d\n"} {
		_, err = io.WriteString(sink, line)
		utest.AssertNil(t, err)
	}

	// #nosec G304 -- test fixture path is derived from t.TempDir()
	active, err := os.ReadFile(filepath.Join(dir, "logger.log"))
	utest.AssertNil(t, err)
	utest.AssertEqual(t, string(active), "d\n")

	// #nosec G304 -- test fixture path is derived from t.TempDir()
	first, err := os.ReadFile(filepath.Join(dir, "logger.log.1"))
	utest.AssertNil(t, err)
	utest.AssertEqual(t, string(first), "c\n")

	// #nosec G304 -- test fixture path is derived from t.TempDir()
	second, err := os.ReadFile(filepath.Join(dir, "logger.log.2"))
	utest.AssertNil(t, err)
	utest.AssertEqual(t, string(second), "b\n")

	_, err = os.Stat(filepath.Join(dir, "logger.log.3"))
	utest.AssertTrue(t, os.IsNotExist(err), "expected third rotated log file to be absent")
}

func TestOpenLogSink_LocalFileCanCompressRotatedFiles(t *testing.T) {
	t.Parallel()

	dir := t.TempDir()
	sink, err := logger.OpenLogSink(logger.LogSinkConfig{
		Kind:      logger.LogSinkKindLocalFile,
		Directory: dir,
		Filename:  "logger.log",
		MaxBytes:  6,
		MaxFiles:  2,
		Compress:  true,
	}, nil)
	utest.AssertNil(t, err)
	defer func() {
		_ = sink.Close()
	}()

	_, err = io.WriteString(sink, "first\n")
	utest.AssertNil(t, err)
	_, err = io.WriteString(sink, "second\n")
	utest.AssertNil(t, err)

	// #nosec G304 -- test fixture path is derived from t.TempDir()
	file, err := os.Open(filepath.Join(dir, "logger.log.1.gz"))
	utest.AssertNil(t, err)
	defer func() {
		_ = file.Close()
	}()

	reader, err := gzip.NewReader(file)
	utest.AssertNil(t, err)
	defer func() {
		_ = reader.Close()
	}()

	content, err := io.ReadAll(reader)
	utest.AssertNil(t, err)
	utest.AssertEqual(t, string(content), "first\n")
}

func TestOpenLogSink_LocalFileRejectsInvalidConfig(t *testing.T) {
	t.Parallel()

	tests := []struct {
		name string
		cfg  logger.LogSinkConfig
	}{
		{
			name: "missing directory",
			cfg: logger.LogSinkConfig{
				Kind:     logger.LogSinkKindLocalFile,
				Filename: "logger.log",
				MaxBytes: 1,
				MaxFiles: 1,
			},
		},
		{
			name: "missing filename",
			cfg: logger.LogSinkConfig{
				Kind:      logger.LogSinkKindLocalFile,
				Directory: t.TempDir(),
				MaxBytes:  1,
				MaxFiles:  1,
			},
		},
		{
			name: "filename contains path separator",
			cfg: logger.LogSinkConfig{
				Kind:      logger.LogSinkKindLocalFile,
				Directory: t.TempDir(),
				Filename:  filepath.Join("nested", "logger.log"),
				MaxBytes:  1,
				MaxFiles:  1,
			},
		},
		{
			name: "missing max bytes",
			cfg: logger.LogSinkConfig{
				Kind:      logger.LogSinkKindLocalFile,
				Directory: t.TempDir(),
				Filename:  "logger.log",
				MaxFiles:  1,
			},
		},
		{
			name: "missing max files",
			cfg: logger.LogSinkConfig{
				Kind:      logger.LogSinkKindLocalFile,
				Directory: t.TempDir(),
				Filename:  "logger.log",
				MaxBytes:  1,
			},
		},
	}

	for _, tc := range tests {
		tc := tc
		t.Run(tc.name, func(t *testing.T) {
			t.Parallel()

			sink, err := logger.OpenLogSink(tc.cfg, nil)
			utest.AssertNotNil(t, err)
			utest.AssertNil(t, sink)
		})
	}
}
