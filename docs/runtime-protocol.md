# Kiln Runtime Protocol

## Status

draft

## Purpose

The runtime protocol exists to let a Python caller safely supervise, initialize, communicate with, shut down, and recover a Go runtime process that performs repository-scale work under Kiln contracts.

The protocol covers:

- JSON-RPC transport over process stdio;
- Python supervision of the Go runtime child process;
- runtime compatibility negotiation;
- runtime health and readiness reporting;
- runtime shutdown and final-exit handling;
- normalized runtime error mapping;
- request correlation and in-flight request disposition;
- runtime session identity;
- runtime session persistence boundaries;
- operation persistence boundaries;
- recovery scan boundaries;
- repository-worker supervision boundary;
- relationship to run, repository, model, budget, capability, artifact, and event contracts.

The protocol does not define a custom Kiln transport envelope. JSON-RPC 2.0 is the external message envelope.

Kiln schemas validate Kiln-owned method params, method results, and Kiln-specific `error.data` payloads.

---

## 1. Architectural boundary

The private runtime boundary has two peers.

| Peer                  | Role                                                                                                                                    |
| --------------------- | --------------------------------------------------------------------------------------------------------------------------------------- |
| Python SDK supervisor | Starts, supervises, initializes, calls, drains, shuts down, and observes the Go runtime process.                                        |
| Go runtime process    | Owns runtime execution, internal routing, repository/model/capability/budget orchestration, persistence, and recoverable runtime state. |

The Python SDK is the process supervisor.

The Go runtime is the protocol server for runtime methods.

Repository workers, model providers, databases, artifact stores, and external services are downstream dependencies of the Go runtime. They are not direct peers of the Python SDK runtime protocol unless explicitly specified by a later protocol.

---

## 2. Protocol layers

The runtime protocol has distinct layers.

| Layer                        | Owner      | Responsibility                                                                |
| ---------------------------- | ---------- | ----------------------------------------------------------------------------- |
| Process supervision          | Python SDK | Spawn process, attach pipes, drain stderr, detect exit, preserve diagnostics. |
| Framing                      | Both       | Encode/decode one JSON-RPC frame per newline.                                 |
| JSON-RPC transport           | Both       | Parse request/response/error envelopes, preserve ids, correlate responses.    |
| Runtime method routing       | Go runtime | Route supported JSON-RPC methods to runtime handlers.                         |
| Kiln contract validation     | Both       | Validate params, results, and Kiln error data against generated schemas.      |
| Runtime lifecycle            | Both       | Initialize, report health, enter draining, shut down, classify final exit.    |
| Runtime persistence/recovery | Go runtime | Persist sessions, operations, ownership leases, and recoverable state.        |

Do not collapse these layers.

A failure in one layer must be reported using that layer’s semantics. For example, unexpected process exit is a supervision failure, not a method-level Kiln response.

---

## 3. Transport

### 3.1 Transport mode

The embedded runtime transport is newline-delimited JSON-RPC 2.0 over child-process stdio.

The Python SDK writes protocol frames to the Go runtime stdin.

The Go runtime writes protocol frames to stdout.

Stdout is protocol-only.

Stderr is diagnostics/logs-only.

No log line, progress message, panic text, or human-readable diagnostic may be written to stdout.

The runtime must not listen on a public interface in embedded SDK mode unless a future transport explicitly defines that mode.

### 3.2 Frame format

Each frame is:

```text
<one UTF-8 JSON object><newline>
```

Rules:

- one JSON object per frame;
- one frame per newline;
- no embedded newline bytes inside a frame;
- blank frames are invalid unless a future transport explicitly permits heartbeats;
- non-object JSON frames are invalid;
- frame size must be bounded before JSON decoding;
- truncated frames before EOF are invalid;
- EOF with no partial frame means stream closed.

### 3.3 JSON-RPC version

The JSON-RPC envelope version is always:

```json
"2.0"
```

The JSON-RPC version is not the Kiln runtime protocol version.

The Kiln runtime protocol version is negotiated through `runtime.initialize.params.protocol_version`.

### 3.4 Request ids

The JSON-RPC `id` is an opaque request-correlation value.

It must not encode:

- run id;
- operation id;
- runtime id;
- repository session id;
- artifact id;
- budget reservation id;
- security/capability identity.

The receiver must echo a usable request id exactly in the response.

If a request id cannot be parsed, parse/invalid-request errors must use `id: null`.

The SDK should use string ids.

Notifications are not part of the initial private runtime protocol unless explicitly added later.

---

## 4. Schema boundary

Kiln does not define JSON-RPC envelope schemas.

Generated Kiln schemas apply to:

- method params;
- method results;
- `error.data` objects;
- domain payloads carried inside method params/results;
- persisted event/artifact/runtime/run records where applicable.

Generated Kiln schemas do not apply to:

- JSON-RPC `jsonrpc`;
- JSON-RPC `id`;
- JSON-RPC `method`;
- JSON-RPC `result` wrapper;
- JSON-RPC `error` wrapper;
- raw stdio framing.

This prevents Kiln from creating a second protocol envelope on top of JSON-RPC.

---

## 5. Versioning and compatibility

The runtime protocol uses separate version concepts.

| Version                  | Meaning                                          | Source                          |
| ------------------------ | ------------------------------------------------ | ------------------------------- |
| JSON-RPC version         | Wire envelope version.                           | Fixed JSON-RPC literal `"2.0"`. |
| Runtime protocol version | Python SDK ↔ Go runtime method compatibility.    | Runtime protocol constant.      |
| Schema-set version       | Generated schema release expected by both peers. | Generated schema metadata.      |
| Compatibility major      | Breaking contract major.                         | Generated schema metadata.      |
| Runtime build version    | Runtime binary/package version.                  | Build metadata.                 |
| SDK version              | Python SDK package version.                      | SDK metadata.                   |

`runtime.initialize` negotiates:

- runtime protocol version;
- schema-set version;
- compatibility major;
- client identity;
- runtime identity;
- supported method surface;
- build metadata.

Compatibility failure must fail closed.

A peer must never infer compatibility from process startup alone.

---

## 6. Runtime session lifecycle

Runtime session lifecycle is the lifecycle of a supervised Go runtime process.

It is not the same as run lifecycle.

```text
not_started
  -> starting
  -> protocol_connected
  -> initializing
  -> ready
  -> draining
  -> exited
```

Failure may occur from any non-terminal state:

```text
starting | protocol_connected | initializing | ready | draining
  -> failed
```

### 6.1 `not_started`

No child process exists.

No protocol calls are valid.

### 6.2 `starting`

The SDK is resolving and spawning the runtime process.

The SDK may collect startup diagnostics.

No runtime method has succeeded.

### 6.3 `protocol_connected`

The process exists and stdio protocol streams are attached.

JSON-RPC frames can be exchanged.

Runtime compatibility is not yet established.

### 6.4 `initializing`

The SDK has sent `runtime.initialize` and is waiting for a valid response.

The runtime is not yet usable.

### 6.5 `ready`

`runtime.initialize` succeeded.

`runtime.health` reports usable readiness.

The SDK may send supported runtime methods.

### 6.6 `draining`

Shutdown has begun or the runtime is refusing new work.

The runtime may continue approved in-flight work or cancel it according to shutdown policy.

New work must be rejected.

### 6.7 `exited`

The child process exited or protocol streams closed.

No more protocol calls are valid on that process session.

### 6.8 `failed`

The runtime failed before graceful exit.

Failure may be due to startup error, initialize failure, malformed protocol behavior, unexpected crash, timeout, forced kill, or unrecoverable internal runtime error.

---

## 7. Runtime methods

The runtime namespace contains process/session control methods.

The full runtime method family is:

| Method               | Purpose                                                                                         |
| -------------------- | ----------------------------------------------------------------------------------------------- |
| `runtime.initialize` | Establish compatibility and runtime session identity.                                           |
| `runtime.health`     | Report readiness, draining, shutdown, and fatal startup state.                                  |
| `runtime.shutdown`   | Request graceful runtime shutdown.                                                              |
| `runtime.status`     | Optional future method for richer runtime/session diagnostics.                                  |
| `runtime.recover`    | Optional future method for explicit recovery actions, if recovery is not solely startup-driven. |

Only implemented methods may be advertised in `supported_methods`.

A runtime must not advertise a method merely because a schema, registry entry, or future issue exists.

The runtime protocol document may define methods before implementation, but `runtime.initialize.result.supported_methods` is a runtime-build capability report, not a roadmap.

---

## 8. `runtime.initialize`

### 8.1 Purpose

`runtime.initialize` establishes a private runtime session between the Python SDK and the Go runtime process.

It is not a security capability exchange.

It does not create a run.

It does not open a repository session.

It does not initialize a repository worker.

It does not authorize model egress.

### 8.2 Params

```json
{
  "protocol_version": "2026-07-01",
  "schema_set_version": "1.0.0",
  "compatibility_major": 1,
  "client": {
    "name": "kiln-python-sdk",
    "version": "0.1.0"
  }
}
```

Required:

| Field                 | Meaning                                           |
| --------------------- | ------------------------------------------------- |
| `protocol_version`    | Runtime protocol version requested by the SDK.    |
| `schema_set_version`  | Schema release expected by the SDK.               |
| `compatibility_major` | Breaking compatibility major expected by the SDK. |
| `client.name`         | Client implementation name.                       |
| `client.version`      | Client implementation version.                    |

### 8.3 Result

```json
{
  "runtime": {
    "id": "runtime_01J...",
    "name": "kiln-runtime",
    "version": "0.1.0"
  },
  "protocol_version": "2026-07-01",
  "schema_set_version": "1.0.0",
  "compatibility_major": 1,
  "supported_method_namespaces": ["runtime", "run", "repository", "model"],
  "supported_methods": [
    "runtime.initialize",
    "runtime.health",
    "runtime.shutdown"
  ],
  "build": {
    "commit": "unknown",
    "date": "2026-07-01T00:00:00Z"
  }
}
```

`runtime.id` is stable for the process session.

`supported_methods` must list methods actually callable in this runtime build.

`supported_method_namespaces` must derive from actually callable methods.

Build metadata is diagnostic only.

### 8.4 Repeated initialization

Repeated initialization with identical params may return the original initialize result.

Repeated initialization with conflicting params must fail with `runtime.already_initialized_with_different_params`.

A conflicting repeated initialize must not mutate established session state.

---

## 9. `runtime.health`

### 9.1 Purpose

`runtime.health` reports runtime readiness and lifecycle state.

It is diagnostic.

It does not create, resume, cancel, or recover runs.

### 9.2 Params

`runtime.health` takes no params.

The protocol should choose one policy and test it consistently:

- strict: omitted `params` only;
- tolerant: omitted `params` or `{}`.

Non-empty params are invalid.

### 9.3 Result

```json
{
  "initialized": true,
  "ready": true,
  "draining": false,
  "shutdown": false,
  "last_fatal_startup_error": null
}
```

Fields:

| Field                      | Meaning                                                           |
| -------------------------- | ----------------------------------------------------------------- |
| `initialized`              | `runtime.initialize` completed successfully.                      |
| `ready`                    | Runtime can accept new work/control requests.                     |
| `draining`                 | Runtime is refusing new work because shutdown or drain has begun. |
| `shutdown`                 | Runtime shutdown has begun or completed.                          |
| `last_fatal_startup_error` | Most recent fatal startup/initialize error, if retained.          |

Invariants:

- `ready` must be false if `draining` is true;
- `ready` must be false if `shutdown` is true;
- `ready` must be false if a fatal startup error prevents initialization;
- `initialized` must become true only after successful initialize;
- a failed initialize must not partially initialize the session.

---

## 10. `runtime.shutdown`

### 10.1 Purpose

`runtime.shutdown` requests deterministic graceful shutdown of the runtime process.

Shutdown coordinates both peers:

- the Python SDK stops issuing new work;
- the Go runtime enters draining;
- policy-approved in-flight work completes or is cancelled;
- protocol resources close in a defined order;
- final exit status is classified and preserved.

### 10.2 Params

Suggested shape:

```json
{
  "grace_period_ms": 30000,
  "cancel_in_flight": true,
  "reason": "caller_requested"
}
```

Fields:

| Field              | Meaning                                                                 |
| ------------------ | ----------------------------------------------------------------------- |
| `grace_period_ms`  | Maximum graceful-drain window before forced termination policy applies. |
| `cancel_in_flight` | Whether runtime should cancel cancellable in-flight operations.         |
| `reason`           | Diagnostic shutdown reason.                                             |

The exact schema may evolve, but shutdown must always be explicit and idempotent.

### 10.3 Result

Suggested shape:

```json
{
  "accepted": true,
  "draining": true,
  "shutdown": false,
  "in_flight_request_count": 1
}
```

The shutdown response confirms that shutdown was accepted. It does not necessarily mean the process has already exited.

Final process exit is observed by the Python supervisor, not by the method response alone.

### 10.4 Idempotency

Repeated shutdown calls must be safe.

If shutdown is already in progress, the runtime should return the current shutdown/draining state.

If the process has already exited, the SDK should treat shutdown as complete and return preserved final exit status rather than attempting a protocol call.

### 10.5 New requests during shutdown

After draining begins:

- new run/repository/model work must be rejected;
- `runtime.health` may be allowed;
- repeated `runtime.shutdown` may be allowed;
- other control methods must be allowed only if explicitly documented.

Rejected calls should use `runtime.draining` or `runtime.shutdown`.

---

## 11. Python supervisor responsibilities

The Python SDK supervisor owns process management.

It must:

- resolve the runtime binary path deterministically;
- avoid relying on the caller’s arbitrary current working directory;
- start the Go runtime child process;
- attach isolated stdin/stdout protocol pipes;
- keep stderr separate from stdout;
- drain stderr throughout the child lifecycle;
- preserve a bounded stderr tail;
- create and manage the JSON-RPC peer;
- perform initialize before marking runtime usable;
- perform health check before marking runtime ready;
- track in-flight requests by JSON-RPC id;
- detect EOF before response;
- detect unexpected child exit;
- preserve exit diagnostics;
- clean up pipes and subprocess resources deterministically.

Supervisor states:

```text
not_started
starting
ready
draining
exited
failed
```

The supervisor must not convert child-process exit into a normal method response.

Unexpected child exit is a supervision/protocol failure.

---

## 12. Go runtime responsibilities

The Go runtime owns server-side method handling and internal runtime orchestration.

It must:

- read JSON-RPC frames from stdin;
- write JSON-RPC frames to stdout;
- keep stdout protocol-only;
- route supported methods;
- validate method params;
- validate method results;
- emit schema-valid Kiln error data;
- maintain runtime session state;
- enter draining on shutdown;
- reject illegal calls by lifecycle state;
- preserve operation disposition;
- own downstream repository/model/budget/capability orchestration;
- persist durable runtime state where required;
- perform startup recovery scans where required.

The Go runtime must not depend on Python for domain consistency once a method has been accepted.

Python supervises the process. Go owns runtime correctness.

---

## 13. Error model

### 13.1 Error layers

Errors belong to one of four layers.

| Layer               | Examples                                                                                 | Representation                                                                  |
| ------------------- | ---------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------- |
| Framing/parse       | invalid JSON, oversized frame, non-object frame                                          | JSON-RPC parse/invalid-request error when possible; otherwise protocol failure. |
| JSON-RPC routing    | method not found, invalid params shape                                                   | JSON-RPC error with optional Kiln error data.                                   |
| Kiln runtime method | compatibility failure, lifecycle rejection, shutdown rejection, internal runtime failure | JSON-RPC error with `error.data.kiln_error`.                                    |
| Supervision/process | EOF before response, unexpected exit, timeout, forced kill                               | Python supervisor exception/result preserving exit diagnostics.                 |

Do not report supervision failures as if the runtime returned a Kiln method error.

### 13.2 Kiln runtime error shape

Runtime method errors must place Kiln semantics under:

```text
error.data.kiln_error
```

Shape:

```json
{
  "code": -32001,
  "message": "Unsupported runtime protocol version",
  "data": {
    "kiln_error": {
      "code": "runtime.unsupported_protocol_version",
      "category": "compatibility",
      "message": "Unsupported runtime protocol version",
      "retryable": false,
      "details": {}
    }
  }
}
```

Stable `kiln_error` fields:

| Field            | Required | Meaning                                            |
| ---------------- | -------: | -------------------------------------------------- |
| `code`           |      yes | Stable dotted Kiln error code.                     |
| `category`       |      yes | Coarse category.                                   |
| `message`        |      yes | Human diagnostic text.                             |
| `retryable`      |      yes | Whether retry may succeed without changing inputs. |
| `details`        |      yes | Structured details object. Empty object when none. |
| `runtime_id`     |       no | Runtime session id when known.                     |
| `correlation_id` |       no | Operation/request correlation id when known.       |

### 13.3 Runtime error categories

| Category        | Meaning                                                     |
| --------------- | ----------------------------------------------------------- |
| `compatibility` | Protocol/schema/compatibility negotiation failed.           |
| `validation`    | Params, result, or error-data validation failed.            |
| `lifecycle`     | Method is illegal in current runtime state.                 |
| `shutdown`      | Runtime is draining/shutting down/shut down.                |
| `internal`      | Runtime failed unexpectedly while handling a valid request. |
| `dependency`    | Downstream repository/model/storage dependency failed.      |
| `recovery`      | Recovery or reconciliation failed.                          |

### 13.4 Runtime error codes

Core runtime codes:

| Code                                                | Meaning                                            |
| --------------------------------------------------- | -------------------------------------------------- |
| `runtime.unsupported_protocol_version`              | Requested runtime protocol version is unsupported. |
| `runtime.incompatible_schema_set_version`           | Requested schema set is unsupported.               |
| `runtime.incompatible_compatibility_major`          | Requested compatibility major is unsupported.      |
| `runtime.already_initialized_with_different_params` | Re-initialize conflicts with established session.  |
| `runtime.method_not_found`                          | Method is not supported by this runtime build.     |
| `runtime.invalid_params`                            | Method params failed validation.                   |
| `runtime.invalid_result`                            | Runtime produced an invalid result.                |
| `runtime.method_requires_initialization`            | Method requires successful initialize.             |
| `runtime.draining`                                  | Runtime is draining and refuses the request.       |
| `runtime.shutdown`                                  | Runtime is shutting down or already shut down.     |
| `runtime.internal_error`                            | Unexpected runtime failure.                        |
| `runtime.dependency_failed`                         | Required downstream dependency failed.             |
| `runtime.recovery_required`                         | Runtime detected recoverable interrupted state.    |
| `runtime.recovery_failed`                           | Runtime recovery failed.                           |

Domain-specific errors should use their own prefixes:

- `run.*`
- `repository.*`
- `model.*`
- `budget.*`
- `capability.*`
- `artifact.*`
- `event.*`

---

## 14. In-flight request disposition

Both peers must treat request disposition as explicit state.

A request may end as:

| Disposition   | Meaning                                                |
| ------------- | ------------------------------------------------------ |
| `succeeded`   | Runtime returned valid result.                         |
| `failed`      | Runtime returned valid JSON-RPC error.                 |
| `cancelled`   | Request was cancelled before completion.               |
| `rejected`    | Request was rejected before execution.                 |
| `interrupted` | Runtime/process ended before final result.             |
| `unknown`     | Process/protocol failure prevents determining outcome. |

Unexpected process exit must preserve the disposition of every in-flight request.

If the runtime cannot prove whether side effects occurred, disposition must not be reported as cleanly cancelled.

---

## 15. Final exit handling

The supervisor must classify final runtime exit.

Exit classes:

| Class | Meaning |
| -------------------- | ----------1----------------------------------------------- |
| `graceful_exit` | Shutdown completed as requested. |
| `protocol_eof` | Stream closed in a context where EOF was expected. |
| `startup_failure` | Runtime failed before becoming usable. |
| `initialize_failure` | Runtime returned or caused initialization failure. |
| `unexpected_exit` | Process exited unexpectedly after startup. |
| `timeout` | Graceful wait exceeded configured deadline. |
| `forced_kill` | Supervisor killed process after timeout or policy breach. |
| `crash` | Process exited abnormally. |

Final exit diagnostics must preserve:

- raw return code;
- normalized exit code;
- normalized signal where available;
- whether exit was expected;
- stderr tail;
- runtime id if known;
- last successful lifecycle state;
- in-flight request dispositions.

---

## 16. Persistence boundary

Runtime persistence is owned by the Go runtime.

The runtime protocol must leave room for durable records without forcing Python to understand storage internals.

Persisted runtime records include:

- runtime sessions;
- ownership leases;
- runs;
- operations;
- attempts;
- causation/correlation;
- authorization decisions;
- budget reservations/usages;
- timing;
- terminal outcomes;
- recovery markers.

The Python SDK may receive summarized state through runtime methods, but it must not directly mutate runtime persistence.

---

## 17. Runtime session persistence

A runtime session record represents a supervised runtime process session.

It should capture:

- runtime session id;
- runtime protocol version;
- schema-set version;
- compatibility major;
- runtime build metadata;
- SDK/client metadata;
- startup time;
- readiness time;
- draining time;
- exit time;
- final exit classification;
- last fatal startup error;
- ownership lease identity where applicable.

Runtime session persistence is necessary for recovery and audit.

It must not be confused with run persistence.

---

## 18. Operation persistence

A runtime operation is a bounded unit of runtime-controlled work.

Operations should persist:

- operation id;
- parent run id;
- operation type;
- attempt number;
- causation id;
- correlation id;
- authorization/capability decision reference;
- budget reservation reference;
- start time;
- finish time;
- outcome;
- error summary;
- artifact references;
- dependency/session references.

Operation persistence exists so cancellation, crash recovery, budget reconciliation, and audit do not depend on process memory.

---

## 19. Startup recovery scan

On startup, the runtime may need to scan durable state for:

- stale runtime sessions;
- non-terminal runs;
- interrupted operations;
- orphaned budget reservations;
- incomplete repository preparation;
- invalidated repository sessions;
- indeterminate model operations;
- artifact integrity failures;
- recoverable ownership leases.

Recovery scan must classify state before resuming or failing work.

Recovery must not silently treat unknown side effects as success.

Recovery must not expose partial repository index state as valid evidence.

---

## 20. Repository-worker boundary

The repository worker is downstream of the Go runtime.

The Python SDK does not supervise repository workers directly through this protocol.

The Go runtime may start, monitor, restart, and stop repository workers through a separate private channel.

Runtime health should not imply repository-worker readiness unless the health schema explicitly reports dependency readiness.

Repository-worker crash handling must preserve:

- committed index state;
- invalidated repository sessions;
- affected operations;
- recovery disposition;
- explicit repository error codes.

---

## 21. Run lifecycle boundary

Runtime lifecycle is not run lifecycle.

A ready runtime is a precondition for run creation/resumption, but it is not itself a run state.

Run lifecycle belongs to run methods and persisted run state.

Runtime protocol may carry run method calls later, but `runtime.initialize`, `runtime.health`, and `runtime.shutdown` must not create or mutate run state except through explicit recovery/shutdown policies.

---

## 22. Model boundary

Model operations are orchestrated by the Go runtime.

The runtime protocol must support model operation cancellation and disposition, but provider-specific model protocols are downstream details.

Model operation outcomes must preserve:

- request artifact reference;
- response artifact reference;
- token counts;
- usage;
- budget reservation/commit/release;
- cancellation status;
- indeterminate status when provider outcome is unknown.

---

## 23. Budget boundary

Budget enforcement belongs inside runtime-controlled operation execution.

The runtime protocol must preserve budget-related operation state enough for:

- preflight reservation;
- usage commit;
- unused release;
- orphaned reservation reconciliation;
- indeterminate usage recording after interruption.

A process crash must not silently lose budget reservations.

---

## 24. Capability and authorization boundary

Runtime initialize is not a capability exchange.

Capability grants, scopes, security profiles, and decisions are domain contracts.

Runtime operations should persist authorization decision references where relevant.

A runtime method may advertise support for a namespace, but method support is not authority to perform the operation.

---

## 25. Artifact and event boundary

The runtime owns durable events and artifacts produced during execution.

The protocol should preserve references to:

- event bounds;
- artifact ids;
- artifact hashes;
- request/response artifacts;
- final result artifacts;
- integrity failures.

Artifact corruption must fail explicitly.

Events and artifacts must be sufficient for audit and replay inspection.

---

## 26. Method advertisement

`runtime.initialize.result.supported_methods` is a runtime-build fact.

It must include only methods that are callable in the current runtime process.

It must not include:

- unimplemented roadmap methods;
- schema-only methods;
- methods registered only in tests;
- downstream worker methods not callable through this runtime protocol;
- methods denied by build-time configuration.

If a method is temporarily disabled by runtime policy, health/status may report that fact separately.

---

## 27. Method namespaces

Expected namespace ownership:

| Namespace      | Owner                     | Meaning                                                  |
| -------------- | ------------------------- | -------------------------------------------------------- |
| `runtime.*`    | Runtime control           | Process/session control, health, shutdown, recovery.     |
| `run.*`        | Runtime domain            | Run creation, status, cancellation, result.              |
| `repository.*` | Runtime/repository worker | Repository sessions, search, source, evidence retrieval. |
| `model.*`      | Runtime/model adapter     | Model generation, cancellation, normalized output.       |
| `budget.*`     | Runtime budget controller | Reservation, usage, reconciliation.                      |
| `capability.*` | Runtime policy layer      | Grants, decisions, scope checks.                         |
| `artifact.*`   | Runtime artifact store    | Artifact references, integrity, retrieval metadata.      |
| `event.*`      | Runtime event log         | Event stream, audit, replay support.                     |

Namespaces do not imply security authority.

---

## 28. Test coverage expectations

The protocol is adequately covered only when tests span the full boundary.

Transport tests:

- valid request/response/error frames;
- malformed JSON;
- blank frames;
- non-object frames;
- oversized frames;
- embedded newlines;
- truncated input;
- EOF behavior;
- multiple frames in one stream.

Runtime method tests:

- initialize success;
- initialize compatibility failures;
- repeated initialize;
- health before/after initialize;
- shutdown success;
- shutdown idempotency;
- shutdown while request is in flight;
- method rejection during draining;
- method rejection after shutdown.

Error mapping tests:

- parse error;
- invalid request;
- invalid params;
- method not found;
- lifecycle rejection;
- shutdown rejection;
- invalid result;
- internal error;
- dependency failure;
- recovery failure.

Supervisor tests:

- missing binary;
- startup success;
- initialize failure;
- malformed runtime response;
- stderr noise;
- stdout contamination failure;
- early exit;
- EOF before response;
- unexpected exit during in-flight request;
- timeout then forced kill;
- final exit diagnostics.

Persistence/recovery tests:

- stale runtime session detection;
- non-terminal run detection;
- interrupted operation classification;
- ownership lease acquisition;
- orphaned budget reconciliation;
- repository preparation recovery;
- artifact integrity failure;
- worker crash classification.

Cross-language contract tests:

- Python and Go validate the same params/results/errors;
- Python and Go preserve JSON-RPC fields without a Kiln envelope;
- Python and Go agree on generated schema compatibility metadata;
- fixture errors validate against runtime error schemas.
