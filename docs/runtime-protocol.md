# Kiln Runtime Protocol

## Status

Draft

## Purpose

This document defines the private protocol between the Python SDK and the supervised Go runtime process.

The runtime protocol is used to:

- initialize a private runtime session;
- negotiate the runtime protocol version, schema-set version, and compatibility major;
- check runtime readiness and shutdown state;
- expose runtime identity and build metadata needed for diagnostics;
- prepare the connection for later run lifecycle methods.

This document does not define:

- repository-worker protocol methods;
- run lifecycle state transitions;
- capability grants or security-profile semantics;
- model-provider contracts;
- a custom Kiln transport envelope.

JSON-RPC is the external message envelope. Kiln schemas validate method params, method results, and Kiln-specific `error.data`.

---

## 1. Transport

The initial embedded transport is MCP-aligned JSON-RPC over stdio.

Each message is a JSON-RPC request, response, or notification. Framing, request-response correlation, and JSON-RPC parse errors are owned by the protocol transport implementation.

Kiln runtime method schemas define only method params, method results, and Kiln-specific error details. They must not redefine the JSON-RPC envelope.

The runtime must not listen on a public interface in embedded SDK mode.

---

## 2. Runtime session lifecycle

The runtime session lifecycle is distinct from the run lifecycle.

```text
process_spawned
  -> protocol_connected
  -> initialized
  -> ready
  -> draining
  -> shutdown
```

### 2.1 `process_spawned`

The Python SDK has started the Go runtime child process.

No Kiln protocol compatibility has been established.

### 2.2 `protocol_connected`

The SDK has attached to the runtime stdio streams and can send JSON-RPC messages.

No Kiln runtime method compatibility has been established.

### 2.3 `initialized`

The SDK has successfully called `runtime.initialize`.

At this point both sides have agreed on:

- runtime protocol version;
- schema-set version;
- compatibility major;
- runtime identity;
- runtime version;
- supported method namespaces;
- diagnostic build metadata.

### 2.4 `ready`

The runtime has reported readiness through `runtime.health`.

A ready runtime may accept later run lifecycle methods.

### 2.5 `draining`

The runtime is shutting down or no longer accepting new work.

Health checks may still return structured status while the process is alive.

### 2.6 `shutdown`

The runtime process has exited or the protocol session has closed.

No further method calls are valid.

---

## 3. Method ordering

The SDK should establish a runtime session in this order:

```text
start runtime process
connect stdio JSON-RPC peer
runtime.initialize
runtime.health
later run methods
shutdown process or close connection
```

`runtime.initialize` must be the first Kiln runtime method called after the JSON-RPC transport is available.

`runtime.health` may be called before initialization only for diagnostics. Before initialization it must not imply that domain methods are safe to call.

The runtime must reject non-health domain methods before successful initialization.

---

## 4. Method: `runtime.initialize`

### 4.1 Purpose

`runtime.initialize` establishes compatibility between the Python SDK and the Go runtime.

It is not a capability exchange. The result may advertise supported method namespaces or runtime features, but authority remains governed by security-profile, scope, grant, and decision contracts.

### 4.2 Params

Conceptual shape:

```json
{
  "protocol_version": "2026-06-30",
  "schema_set_version": "v1",
  "compatibility_major": 1,
  "client": {
    "name": "kiln-python-sdk",
    "version": "0.1.0"
  }
}
```

Required fields:

| Field | Meaning |
| --- | --- |
| `protocol_version` | Runtime protocol version requested by the SDK. |
| `schema_set_version` | Schema set expected by the SDK. |
| `compatibility_major` | Breaking-compatibility major version. |
| `client.name` | SDK or client name for diagnostics. |
| `client.version` | SDK or client version for diagnostics. |

### 4.3 Result

Conceptual shape:

```json
{
  "runtime": {
    "id": "runtime_...",
    "name": "kiln-go-runtime",
    "version": "0.1.0"
  },
  "protocol_version": "2026-06-30",
  "schema_set_version": "v1",
  "compatibility_major": 1,
  "supported_method_namespaces": [
    "runtime"
  ],
  "supported_methods": [
    "runtime.initialize",
    "runtime.health"
  ],
  "build": {
    "commit": "unknown",
    "date": "unknown"
  }
}
```

Required result semantics:

- `runtime.id` is stable for the runtime process session.
- `runtime.name` identifies the runtime implementation.
- `runtime.version` identifies the runtime build version.
- `protocol_version` is the negotiated protocol version.
- `schema_set_version` is the negotiated schema-set version.
- `compatibility_major` is the negotiated compatibility major.
- `supported_method_namespaces` advertises method namespaces, not security capabilities.
- `supported_methods` advertises specific JSON-RPC methods currently supported by the runtime.
- `build` contains diagnostic metadata and must not be used for authorization.

### 4.4 Repeated initialization

A repeated `runtime.initialize` request with identical compatibility params may return the same initialized result.

A repeated `runtime.initialize` request with conflicting compatibility params must fail closed.

### 4.5 Failure behavior

The runtime must fail closed when compatibility cannot be established.

Unsupported runtime protocol version:

```json
{
  "code": -32001,
  "message": "Unsupported runtime protocol version",
  "data": {
    "kiln_error_code": "runtime.unsupported_protocol_version",
    "requested_protocol_version": "2026-01-01",
    "supported_protocol_versions": ["2026-06-30"]
  }
}
```

Incompatible schema-set version:

```json
{
  "code": -32002,
  "message": "Incompatible schema-set version",
  "data": {
    "kiln_error_code": "runtime.incompatible_schema_set_version",
    "requested_schema_set_version": "v0",
    "supported_schema_set_versions": ["v1"]
  }
}
```

Incompatible compatibility major:

```json
{
  "code": -32003,
  "message": "Incompatible runtime compatibility major",
  "data": {
    "kiln_error_code": "runtime.incompatible_compatibility_major",
    "requested_compatibility_major": 0,
    "supported_compatibility_majors": [1]
  }
}
```

Malformed params use the project JSON-RPC validation error shape.

---

## 5. Method: `runtime.health`

### 5.1 Purpose

`runtime.health` reports whether the runtime process is currently able to accept work.

It is a diagnostic and readiness method. It does not create a run, resume a run, or grant authority.

### 5.2 Params

Conceptual shape:

```json
{}
```

### 5.3 Result

Conceptual shape:

```json
{
  "initialized": true,
  "ready": true,
  "draining": false,
  "shutdown": false,
  "last_fatal_startup_error": null
}
```

Required fields:

| Field | Meaning |
| --- | --- |
| `initialized` | `runtime.initialize` completed successfully. |
| `ready` | Runtime can accept new work. |
| `draining` | Runtime is shutting down or refusing new work. |
| `shutdown` | Runtime has entered shutdown state or observed process shutdown. |
| `last_fatal_startup_error` | Structured fatal startup error, when present. |

### 5.4 Health state matrix

| Runtime condition | `initialized` | `ready` | `draining` | `shutdown` |
| --- | ---: | ---: | ---: | ---: |
| Before initialize | false | false | false | false |
| Initialized and usable | true | true | false | false |
| Startup failed | false | false | false | false |
| Draining | true | false | true | false |
| Shutdown observed | true/false | false | false/true | true |

When `last_fatal_startup_error` is present, `ready` must be false.

---

## 6. Relationship to run lifecycle

Runtime lifecycle is process/session lifecycle.

Run lifecycle is task execution lifecycle.

A healthy initialized runtime is a precondition for creating or resuming a run, but it is not itself a run state transition.

The run lifecycle begins only when a run specification is accepted and a run enters `created`.

---

## 7. Relationship to repository-worker protocol

The runtime protocol governs Python SDK to Go runtime communication.

The repository-worker protocol governs Go runtime to repository worker communication.

The repository-worker handshake is a separate milestone and must not be implemented as part of `runtime.initialize`.

---

## 8. Out of scope for CYB-206

CYB-206 defines only the runtime initialization and health control plane.

Out of scope:

- repository operation dispatch;
- run creation;
- run cancellation;
- run status streaming;
- run result retrieval;
- capability broker implementation;
- repository-worker handshake;
- custom Kiln protocol-envelope schemas;
- process-supervisor hardening beyond what is needed to carry stdio JSON-RPC.
