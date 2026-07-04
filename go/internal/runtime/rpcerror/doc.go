// Package runtimeerror defines structured runtime error specifications and
// helpers for producing protocol-compatible JSON-RPC error objects.
//
// It centralizes Kiln runtime error metadata including:
// - JSON-RPC and Kiln-specific error codes
// - error categories (compatibility, validation, lifecycle, shutdown, internal)
// - retryability and optional detail payloads
//
// The package is used by runtime handlers and orchestration code to return
// consistent, contract-aligned error responses.
package rpcerror
