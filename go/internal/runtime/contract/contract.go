package contract

import (
	"context"

	"github.com/julianstephens/kiln/go/internal/protocol"
)

type Handler func(context.Context, protocol.Request) protocol.Message

type RuntimeDeps struct {
	Build BuildInfo
	// Add other shared deps here
}

const (
	RuntimeProtocolVersion = "2026-07-01"
	RuntimeName            = "kiln-runtime"

	JSONRPCInvalidRequest = -32600
	JSONRPCMethodNotFound = -32601
	JSONRPCInvalidParams  = -32602
	JSONRPCInternalError  = -32603
	JSONRPCParseError     = -32700

	KilnRuntimeUnsupportedProtocolVersion            = -32001
	KilnRuntimeIncompatibleSchemaSetVersion          = -32002
	KilnRuntimeIncompatibleCompatibilityMajor        = -32003
	KilnRuntimeAlreadyInitializedWithDifferentParams = -32004
)
