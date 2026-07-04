// Package contract defines the shared types and constants for the runtime system.
// It serves as the type boundary to prevent import cycles:
// - contract has no external dependencies
// - handler imports contract
// - runtime imports both contract and handler
package contract
