package contract

import (
	"context"
	"log/slog"

	"github.com/julianstephens/kiln/go/internal/persistence"
	"github.com/julianstephens/kiln/go/internal/protocol"
)

type Handler func(context.Context, protocol.Request) protocol.Message

type RuntimeDeps struct {
	Build           BuildInfo
	Lifecycle       *Lifecycle
	Logger          *slog.Logger
	PendingRequests *protocol.PendingRequests
	Store           persistence.Store
}

const (
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
