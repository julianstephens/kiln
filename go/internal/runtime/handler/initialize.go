package handler

import (
	"context"
	"fmt"

	"github.com/julianstephens/kiln/go/internal/protocol"
	"github.com/julianstephens/kiln/go/internal/runtime/contract"
	"github.com/julianstephens/kiln/go/internal/util"
	"github.com/julianstephens/kiln/go/schema"
	runtime_error "github.com/julianstephens/kiln/go/schema/runtime/error"
	"github.com/julianstephens/kiln/go/schema/runtime/initialize_request_payload"
	"github.com/julianstephens/kiln/go/schema/runtime/initialize_result"
	"github.com/oklog/ulid/v2"
)

// MakeInitializeHandler returns a Handler closure that captures state and deps.
func MakeInitializeHandler(state *HandlerState, deps *contract.RuntimeDeps) contract.Handler {
	return func(ctx context.Context, req protocol.Request) protocol.Message {
		state.Mu.Lock()
		defer state.Mu.Unlock()

		if deps != nil && deps.Logger != nil {
			deps.Logger.Debug("initialize request received",
				"request_id", req.ID.JSONValue(),
				"params", req.Params,
			)
		}

		res, err := protocol.KilnMethods["runtime.initialize"].ValidateParams(req.Params)
		if err != nil {
			if deps != nil && deps.Logger != nil {
				deps.Logger.Debug("initialize request validation failed",
					"request_id", req.ID.JSONValue(),
					"params", req.Params,
					"error", err.Error(),
				)
			}
			kilnErr := invalidRequestParamsError(req.Params)
			state.LastFatalStartupError = &kilnErr.Data.KilnError
			return protocol.NewErrorResponse(req.ID, kilnErr)
		}

		validatedParams, ok := res.(*initialize_request_payload.InitializeRequestPayload)
		if !ok {
			if deps != nil && deps.Logger != nil {
				deps.Logger.Debug("initialize request validation returned unexpected type",
					"request_id", req.ID.JSONValue(),
					"params", req.Params,
					"validated_type", fmt.Sprintf("%T", res),
				)
			}
			kilnErr := invalidRequestParamsError(req.Params)
			state.LastFatalStartupError = &kilnErr.Data.KilnError
			return protocol.NewErrorResponse(req.ID, kilnErr)
		}

		if deps != nil && deps.Logger != nil {
			deps.Logger.Debug("initialize request validated",
				"request_id", req.ID.JSONValue(),
				"protocol_version", validatedParams.ProtocolVersion,
				"schema_set_version", validatedParams.SchemaSetVersion,
				"compatibility_major", validatedParams.CompatibilityMajor,
				"client_name", validatedParams.Client.Name,
				"client_version", validatedParams.Client.Version,
			)
		}

		if state.Initialized {
			if sameInitializeParams(state.InitialParams, *validatedParams) {
				return protocol.NewSuccessResponse(req.ID, util.StructToMap(state.InitialResult))
			}
			kilnErr := alreadyInitializedWithDifferentParams(util.StructToMap(state.InitialParams), req.Params)
			state.LastFatalStartupError = &kilnErr.Data.KilnError
			return protocol.NewErrorResponse(req.ID, kilnErr)
		}

		switch {
		case validatedParams.ProtocolVersion != contract.RuntimeProtocolVersion:
			kilnErr := unsupportedProtocolVersionError(validatedParams.ProtocolVersion)
			state.LastFatalStartupError = &kilnErr.Data.KilnError
			return protocol.NewErrorResponse(req.ID, kilnErr)
		case validatedParams.SchemaSetVersion != schema.SchemaSetVersion:
			kilnErr := incompatibleSchemaSetVersionError(validatedParams.SchemaSetVersion)
			state.LastFatalStartupError = &kilnErr.Data.KilnError
			return protocol.NewErrorResponse(req.ID, kilnErr)
		case validatedParams.CompatibilityMajor != schema.CompatibilityMajor:
			kilnErr := incompatibleCompatibilityMajor(validatedParams.CompatibilityMajor)
			state.LastFatalStartupError = &kilnErr.Data.KilnError
			return protocol.NewErrorResponse(req.ID, kilnErr)
		}

		result := initialize_result.InitializeResult{
			Runtime: initialize_result.InitializeResultRuntime{
				ID:      newRuntimeID(),
				Name:    contract.RuntimeName,
				Version: deps.Build.Version,
			},
			ProtocolVersion:           contract.RuntimeProtocolVersion,
			SchemaSetVersion:          schema.SchemaSetVersion,
			CompatibilityMajor:        schema.CompatibilityMajor,
			SupportedMethodNamespaces: protocol.SupportedMethodNamespaces(),
			SupportedMethods:          protocol.SupportedMethods(),
			Build: initialize_result.InitializeResultBuild{
				Commit: deps.Build.Commit,
				Date:   deps.Build.Date,
			},
		}

		state.Initialized = true
		state.Ready = true
		state.InitialParams = *validatedParams
		state.InitialResult = result

		return protocol.NewSuccessResponse(req.ID, util.StructToMap(result))
	}
}

func newRuntimeID() string {
	return fmt.Sprintf("runtime_%s", ulid.Make().String())
}

func sameInitializeParams(
	a initialize_request_payload.InitializeRequestPayload,
	b initialize_request_payload.InitializeRequestPayload,
) bool {
	return a.ProtocolVersion == b.ProtocolVersion &&
		a.SchemaSetVersion == b.SchemaSetVersion &&
		a.CompatibilityMajor == b.CompatibilityMajor &&
		a.Client.Name == b.Client.Name &&
		a.Client.Version == b.Client.Version
}

func invalidRequestParamsError(requested map[string]any) protocol.ErrorObject {
	return protocol.ErrorObject{
		Code:    contract.JSONRPCInvalidParams,
		Message: "Invalid request params",
		Data: runtime_error.Error{
			KilnError: runtime_error.ErrorKilnError{
				Category:  "validation",
				Code:      "runtime.invalid_initialize_params",
				Message:   "Invalid initialize params",
				Retryable: false,
				Details: map[string]any{
					"params": requested,
				},
			},
		},
	}
}

func unsupportedProtocolVersionError(requested string) protocol.ErrorObject {
	return protocol.ErrorObject{
		Code:    contract.KilnRuntimeUnsupportedProtocolVersion,
		Message: "Unsupported runtime protocol version",
		Data: runtime_error.Error{
			KilnError: runtime_error.ErrorKilnError{
				Category:  "compatibility",
				Code:      "runtime.unsupported_protocol_version",
				Message:   "Unsupported runtime protocol version",
				Retryable: false,
				Details: map[string]any{
					"requested_protocol_version":  requested,
					"supported_protocol_versions": []string{contract.RuntimeProtocolVersion},
				},
			},
		},
	}
}

func incompatibleSchemaSetVersionError(requested string) protocol.ErrorObject {
	return protocol.ErrorObject{
		Code:    contract.KilnRuntimeIncompatibleSchemaSetVersion,
		Message: "Incompatible schema set version",
		Data: runtime_error.Error{
			KilnError: runtime_error.ErrorKilnError{
				Category:  "compatibility",
				Code:      "runtime.incompatible_schema_set_version",
				Message:   "Incompatible schema set version",
				Retryable: false,
				Details: map[string]any{
					"requested_schema_set_version":  requested,
					"supported_schema_set_versions": []string{schema.SchemaSetVersion},
				},
			},
		},
	}
}

func incompatibleCompatibilityMajor(requested int) protocol.ErrorObject {
	return protocol.ErrorObject{
		Code:    contract.KilnRuntimeIncompatibleCompatibilityMajor,
		Message: "Incompatible compatibility major",
		Data: runtime_error.Error{
			KilnError: runtime_error.ErrorKilnError{
				Category:  "compatibility",
				Code:      "runtime.incompatible_compatibility_major",
				Message:   "Incompatible compatibility major",
				Retryable: false,
				Details: map[string]any{
					"requested_compatibility_major":  requested,
					"supported_compatibility_majors": []int{schema.CompatibilityMajor},
				},
			},
		},
	}
}

func alreadyInitializedWithDifferentParams(
	originalParams map[string]any,
	requestedParams map[string]any,
) protocol.ErrorObject {
	return protocol.ErrorObject{
		Code:    contract.KilnRuntimeAlreadyInitializedWithDifferentParams,
		Message: "Runtime already initialized with different params",
		Data: runtime_error.Error{
			KilnError: runtime_error.ErrorKilnError{
				Category:  "validation",
				Code:      "runtime.already_initialized_with_different_params",
				Message:   "Runtime already initialized with different params",
				Retryable: false,
				Details: map[string]any{
					"original_params":  originalParams,
					"requested_params": requestedParams,
				},
			},
		},
	}
}
