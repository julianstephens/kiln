// Package runtime implements the JSON-RPC server loop and handler routing.
// It coordinates between the protocol layer, handler implementations, and persistence.
//
// Architecture:
// - contract: shared types (Handler, RuntimeDeps, constants)
// - handler: handler implementations
// - runtime: main loop, router, and orchestration
package runtime
