// Package protocol implements JSON-RPC 2.0 message framing, parsing, and validation.
//
// It provides:
// - Message types: Request, SuccessResponse, ErrorResponse
// - Message parsing and serialization
// - Method registry (KilnMethods) for param/result/error validation
// - Peer abstraction for bidirectional message I/O over stdio
// - Pending request tracking for request-response correlation
//
// The protocol package has no dependencies on runtime or handler packages,
// making it a pure transport and serialization layer.
package protocol
