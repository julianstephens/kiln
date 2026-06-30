package protocol_test

import (
	"fmt"
	"testing"

	utest "github.com/julianstephens/go-utils/tests"

	"github.com/julianstephens/kiln/go/internal/protocol"
)

func methodSpecForExternalInput(method string) (protocol.MethodSpec, error) {
	spec, ok := protocol.KilnMethods[method]
	if !ok {
		return protocol.MethodSpec{}, fmt.Errorf("unsupported method: %s", method)
	}
	return spec, nil
}

func validateSearchParamsExternal(method string, params map[string]any) (any, error) {
	spec, err := methodSpecForExternalInput(method)
	if err != nil {
		return nil, err
	}
	return spec.ValidateParams(params)
}

func validateSearchResultExternal(method string, result map[string]any) (any, error) {
	spec, err := methodSpecForExternalInput(method)
	if err != nil {
		return nil, err
	}
	return spec.ValidateResult(result)
}

func validateSearchErrorDataExternal(method string, data map[string]any) (any, error) {
	spec, err := methodSpecForExternalInput(method)
	if err != nil {
		return nil, err
	}

	validated, err := spec.ValidateErrorData(data)
	if err != nil {
		return nil, fmt.Errorf("invalid error.data: %w", err)
	}

	return validated, nil
}

func TestRepositorySearchValidation_ExternalMethod_TableDriven(t *testing.T) {
	t.Parallel()

	validParams := map[string]any{
		"query": "schema generator",
		"mode":  "hybrid",
		"limit": 10,
	}
	invalidParams := map[string]any{
		"mode":  "hybrid",
		"limit": 10,
	}

	validResult := map[string]any{
		"candidates":   []any{},
		"result_count": 1,
		"truncated":    true,
	}

	validErrorData := map[string]any{
		"artifact_references":   []any{},
		"category":              "search",
		"code":                  "repo_search_error",
		"diagnostics":           []any{},
		"message":               "search failed",
		"operation_id":          "op-1",
		"repository_session_id": "session-1",
		"repository_version":    map[string]any{},
		"retryable":             true,
		"workspace_version":     map[string]any{},
	}
	invalidErrorData := map[string]any{
		"artifact_references":   []any{},
		"category":              "search",
		"code":                  "repo_search_error",
		"diagnostics":           []any{},
		"operation_id":          "op-1",
		"repository_session_id": "session-1",
		"repository_version":    map[string]any{},
		"retryable":             false,
		"workspace_version":     map[string]any{},
	}

	tests := []struct {
		name            string
		run             func() (any, error)
		wantErrContains string
	}{
		{
			name: "unknown method rejected as unsupported method",
			run: func() (any, error) {
				return validateSearchParamsExternal("repository.unknown", validParams)
			},
			wantErrContains: "unsupported method",
		},
		{
			name: "repository.search params validated against RepositorySearchRequestPayload",
			run: func() (any, error) {
				return validateSearchParamsExternal("repository.search", validParams)
			},
		},
		{
			name: "repository.search params invalid payload rejected",
			run: func() (any, error) {
				return validateSearchParamsExternal("repository.search", invalidParams)
			},
			wantErrContains: "required",
		},
		{
			name: "repository.search result validated when method supplied externally",
			run: func() (any, error) {
				return validateSearchResultExternal("repository.search", validResult)
			},
		},
		{
			name: "repository.search error.data validated when method supplied externally",
			run: func() (any, error) {
				return validateSearchErrorDataExternal("repository.search", validErrorData)
			},
		},
		{
			name: "invalid error.data wrapped consistently",
			run: func() (any, error) {
				return validateSearchErrorDataExternal("repository.search", invalidErrorData)
			},
			wantErrContains: "invalid error.data:",
		},
	}

	for _, tc := range tests {
		tc := tc
		t.Run(tc.name, func(t *testing.T) {
			t.Parallel()

			got, err := tc.run()
			if tc.wantErrContains == "" {
				utest.RequireNoError(t, err)
				utest.AssertNotNil(t, got)
				return
			}

			utest.AssertNotNil(t, err)
			utest.AssertErrorContains(t, err, tc.wantErrContains)
			utest.AssertNil(t, got)
		})
	}
}
