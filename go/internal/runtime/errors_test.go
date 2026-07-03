package runtime_test

import (
	"testing"

	utest "github.com/julianstephens/go-utils/tests"

	"github.com/julianstephens/kiln/go/internal/runtime"
)

func TestError_ErrorString_TableDriven(t *testing.T) {
	t.Parallel()

	tests := []struct {
		name string
		err  *runtime.Error
		want string
	}{
		{
			name: "without details",
			err: &runtime.Error{
				Code:    "runtime.test",
				Message: "failed",
			},
			want: "runtime.test: failed",
		},
		{
			name: "with details",
			err: &runtime.Error{
				Code:    "runtime.test",
				Message: "failed",
				Details: "some detail",
			},
			want: "runtime.test: failed (some detail)",
		},
	}

	for _, tc := range tests {
		tc := tc
		t.Run(tc.name, func(t *testing.T) {
			t.Parallel()

			utest.AssertEqual(t, tc.err.Error(), tc.want)
		})
	}
}
