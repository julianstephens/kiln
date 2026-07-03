package protocol

import (
	"encoding/json"
	"slices"
	"strings"

	model_error "github.com/julianstephens/kiln/go/schema/model/error"
	model_generate_payload "github.com/julianstephens/kiln/go/schema/model/generate_payload"
	model_generate_result "github.com/julianstephens/kiln/go/schema/model/generate_result"
	repository_error "github.com/julianstephens/kiln/go/schema/repository/error"
	repository_open_session_request_payload "github.com/julianstephens/kiln/go/schema/repository/open_session_request_payload"
	repository_search_request_payload "github.com/julianstephens/kiln/go/schema/repository/search_request_payload"
	repository_search_result "github.com/julianstephens/kiln/go/schema/repository/search_result"
	repository_session "github.com/julianstephens/kiln/go/schema/repository/session"
	repository_source_request_payload "github.com/julianstephens/kiln/go/schema/repository/source_request_payload"
	repository_source_result "github.com/julianstephens/kiln/go/schema/repository/source_result"
	runtime_error "github.com/julianstephens/kiln/go/schema/runtime/error"
	"github.com/julianstephens/kiln/go/schema/runtime/health_result"
	"github.com/julianstephens/kiln/go/schema/runtime/initialize_request_payload"
	"github.com/julianstephens/kiln/go/schema/runtime/initialize_result"
)

type MethodSpec struct {
	Method string

	ValidateParams    func(map[string]any) (any, error)
	ValidateResult    func(map[string]any) (any, error)
	ValidateErrorData func(map[string]any) (any, error)
}

var KilnMethods = map[string]MethodSpec{
	"runtime.initialize": {
		Method: "runtime.initialize",
		ValidateParams: func(v map[string]any) (any, error) {
			return validateAs[initialize_request_payload.InitializeRequestPayload](v)
		},
		ValidateResult: func(v map[string]any) (any, error) {
			return validateAs[initialize_result.InitializeResult](v)
		},
		ValidateErrorData: func(v map[string]any) (any, error) {
			return validateAs[runtime_error.Error](v)
		},
	},
	"runtime.health": {
		Method: "runtime.health",
		ValidateResult: func(v map[string]any) (any, error) {
			return validateAs[health_result.HealthResult](v)
		},
		ValidateErrorData: func(v map[string]any) (any, error) {
			return validateAs[runtime_error.Error](v)
		},
	},
	"repository.open_session": {
		Method: "repository.open_session", ValidateParams: func(v map[string]any) (any, error) {
			return validateAs[repository_open_session_request_payload.OpenSessionRequestPayload](v)
		},
		ValidateResult: func(v map[string]any) (any, error) {
			return validateAs[repository_session.Session](v)
		},
		ValidateErrorData: func(v map[string]any) (any, error) {
			return validateAs[repository_error.Error](v)
		},
	},
	"repository.search": {
		Method: "repository.search",
		ValidateParams: func(v map[string]any) (any, error) {
			return validateAs[repository_search_request_payload.SearchRequestPayload](v)
		},
		ValidateResult: func(v map[string]any) (any, error) {
			return validateAs[repository_search_result.SearchResult](v)
		},
		ValidateErrorData: func(v map[string]any) (any, error) {
			return validateAs[repository_error.Error](v)
		},
	},
	"repository.get_source": {
		Method: "repository.get_source",
		ValidateParams: func(v map[string]any) (any, error) {
			return validateAs[repository_source_request_payload.SourceRequestPayload](v)
		},
		ValidateResult: func(v map[string]any) (any, error) {
			return validateAs[repository_source_result.SourceResult](v)
		},
		ValidateErrorData: func(v map[string]any) (any, error) {
			return validateAs[repository_error.Error](v)
		},
	},
	"model.generate": {
		Method: "model.generate",
		ValidateParams: func(v map[string]any) (any, error) {
			return validateAs[model_generate_payload.GeneratePayload](v)
		},
		ValidateResult: func(v map[string]any) (any, error) {
			return validateAs[model_generate_result.GenerateResult](v)
		},
		ValidateErrorData: func(v map[string]any) (any, error) {
			return validateAs[model_error.Error](v)
		},
	},
}

func validateAs[T interface{ Validate() error }](value map[string]any) (*T, error) {
	data, err := json.Marshal(value)
	if err != nil {
		return nil, err
	}

	var typed T
	if err := json.Unmarshal(data, &typed); err != nil {
		return nil, err
	}

	if err := typed.Validate(); err != nil {
		return nil, err
	}

	return &typed, nil
}

// SupportedMethods returns a slice of all supported method names in the KilnMethods map.
func SupportedMethods() []string {
	res := make([]string, 0, len(KilnMethods))
	for k := range KilnMethods {
		res = append(res, k)
	}
	return res
}

// SupportedMethodNamespaces returns a slice of unique namespaces for all supported methods in the KilnMethods map.
func SupportedMethodNamespaces() []string {
	res := make([]string, 0)
	for k := range KilnMethods {
		namespace := k[:strings.Index(k, ".")]
		if !slices.Contains(res, namespace) {
			res = append(res, namespace)
		}
	}
	return res
}
