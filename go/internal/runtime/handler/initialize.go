package handler

import (
	"context"
	"fmt"

	"github.com/julianstephens/kiln/go/internal/protocol"
	"github.com/julianstephens/kiln/go/internal/runtime/contract"
	"github.com/julianstephens/kiln/go/internal/runtime/rpcerror"
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
		if deps != nil && deps.Logger != nil {
			deps.Logger.Debug("initialize request received",
				"request_id", req.ID.JSONValue(),
				"params", req.Params,
			)
		}

		initMethod := protocol.KilnMethods["runtime.initialize"]

		res, err := initMethod.ValidateParams(req.Params)
		if err != nil {
			if deps != nil && deps.Logger != nil {
				deps.Logger.Debug("initialize request validation failed",
					"request_id", req.ID.JSONValue(),
					"params", req.Params,
					"error", err.Error(),
				)
			}
			errRes, kilnErr := rpcerror.InvalidParams(req.ID, req.Method, map[string]any{
				"params": req.Params,
			})
			state.SetLastFatalStartupError(&kilnErr)
			return errRes
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
			errRes, kilnErr := rpcerror.Internal(
				req.ID,
				&req.Method,
				"initialize params validator returned unexpected type",
				map[string]any{
					"params":         req.Params,
					"validated_type": fmt.Sprintf("%T", res),
				},
			)
			state.SetLastFatalStartupError(&kilnErr)
			return errRes
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

		if state.IsInitialized() {
			if sameInitializeParams(state.GetInitialParams(), *validatedParams) {
				return protocol.NewSuccessResponse(req.ID, util.MustStructToMap(state.GetInitialResult()))
			}
			spec := rpcerror.Spec{
				JSONRPCCode: contract.KilnRuntimeAlreadyInitializedWithDifferentParams,
				KilnCode:    "runtime.already_initialized_with_different_params",
				Method:      "runtime.initialize",
				Category:    runtime_error.ErrorKilnErrorCategoryValidation,
				Message:     "Runtime already initialized with different params",
				Retryable:   false,
				Details: map[string]any{
					"original_params":  util.MustStructToMap(state.GetInitialParams()),
					"requested_params": util.MustStructToMap(validatedParams),
				},
			}
			errRes, _ := rpcerror.Response(req.ID, spec)
			return errRes
		}

		switch {
		case validatedParams.ProtocolVersion != contract.RuntimeProtocolVersion:
			spec := rpcerror.Spec{
				JSONRPCCode: contract.KilnRuntimeUnsupportedProtocolVersion,
				KilnCode:    "runtime.unsupported_protocol_version",
				Method:      "runtime.initialize",
				Category:    runtime_error.ErrorKilnErrorCategoryCompatibility,
				Message:     "unsupported runtime protocol version",
				Retryable:   false,
				Details: map[string]any{
					"requested_protocol_version":  validatedParams.ProtocolVersion,
					"supported_protocol_versions": []string{contract.RuntimeProtocolVersion},
				},
			}
			errRes, kilnErr := rpcerror.Response(req.ID, spec)
			state.SetLastFatalStartupError(&kilnErr)
			return errRes
		case validatedParams.SchemaSetVersion != schema.SchemaSetVersion:
			spec := rpcerror.Spec{
				JSONRPCCode: contract.KilnRuntimeIncompatibleSchemaSetVersion,
				KilnCode:    "runtime.incompatible_schema_set_version",
				Category:    runtime_error.ErrorKilnErrorCategoryCompatibility,
				Message:     "Incompatible schema set version",
				Retryable:   false,
				Details: map[string]any{
					"requested_schema_set_version":  validatedParams.SchemaSetVersion,
					"supported_schema_set_versions": []string{schema.SchemaSetVersion},
				},
			}
			errRes, kilnErr := rpcerror.Response(req.ID, spec)
			state.SetLastFatalStartupError(&kilnErr)
			return errRes
		case validatedParams.CompatibilityMajor != schema.CompatibilityMajor:
			spec := rpcerror.Spec{
				JSONRPCCode: contract.KilnRuntimeIncompatibleCompatibilityMajor,
				KilnCode:    "runtime.incompatible_compatibility_major",
				Category:    runtime_error.ErrorKilnErrorCategoryCompatibility,
				Message:     "Incompatible compatibility major",
				Retryable:   false,
				Details: map[string]any{
					"requested_compatibility_major":  validatedParams.CompatibilityMajor,
					"supported_compatibility_majors": []int{schema.CompatibilityMajor},
				},
			}
			errRes, kilnErr := rpcerror.Response(req.ID, spec)
			state.SetLastFatalStartupError(&kilnErr)
			return errRes
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

		state.SetInitialized(true)
		state.SetReady(true)
		state.SetInitialParams(*validatedParams)
		state.SetInitialResult(result)

		return protocol.NewSuccessResponse(req.ID, util.MustStructToMap(result))
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
