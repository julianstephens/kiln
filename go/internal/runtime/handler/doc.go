// Package handler provides JSON-RPC method implementations for the runtime.
// Each handler is a factory function that returns a Handler closure,
// capturing runtime state and dependencies through closure.
// Handlers should only import contract, not the runtime package.
package handler
