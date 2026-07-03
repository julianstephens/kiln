package runtime_test

import (
	"bytes"
	"context"
	"testing"

	utest "github.com/julianstephens/go-utils/tests"

	"github.com/julianstephens/kiln/go/internal/runtime"
)

func TestRun_Preconditions_TableDriven(t *testing.T) {
	t.Parallel()

	tests := []struct {
		name    string
		cfg     runtime.Config
		wantErr *runtime.Error
	}{
		{
			name: "missing input stream returns expected error",
			cfg: runtime.Config{
				Input:  nil,
				Output: &bytes.Buffer{},
			},
			wantErr: runtime.ErrInputStreamMissing,
		},
		{
			name: "missing output stream returns expected error",
			cfg: runtime.Config{
				Input:  bytes.NewBuffer(nil),
				Output: nil,
			},
			wantErr: runtime.ErrOutputStreamMissing,
		},
		{
			name: "invalid log sink config returns expected error",
			cfg: runtime.Config{
				Input:  bytes.NewBuffer(nil),
				Output: &bytes.Buffer{},
				LogSink: runtime.LogSinkConfig{
					Kind:     runtime.LogSinkKindLocalFile,
					Filename: "runtime.log",
					MaxBytes: 1,
					MaxFiles: 1,
				},
			},
			wantErr: &runtime.Error{
				Code:    runtime.CodeLogSinkOpenFailed,
				Message: "failed to open log sink",
			},
		},
	}

	for _, tc := range tests {
		tc := tc
		t.Run(tc.name, func(t *testing.T) {
			t.Parallel()

			err := runtime.Run(context.Background(), tc.cfg)
			utest.AssertNotNil(t, err)

			runtimeErr, ok := err.(*runtime.Error)
			utest.AssertTrue(t, ok, "expected *runtime.Error")
			if ok {
				utest.AssertEqual(t, runtimeErr.Code, tc.wantErr.Code)
				utest.AssertEqual(t, runtimeErr.Message, tc.wantErr.Message)
			}
		})
	}
}
