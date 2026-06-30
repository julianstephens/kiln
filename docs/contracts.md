# Kiln Core Contracts

## Status

Draft

## Purpose

This document defines the semantic contracts shared across Kiln's runtime, Python SDK, repository engine, validation package, and hosted integrations.

It describes:

- what each core object represents;
- which component owns it;
- who may create or mutate it;
- the states it may enter;
- the invariants that must always hold;
- how objects relate to one another.

It intentionally does not prescribe:

- Go or Python type definitions;
- database tables;
- JSON schemas;
- wire encodings;
- provider-specific fields;
- package layout.

Those implementation artifacts should conform to the semantics defined here.

---

## 1. Contract conventions

### 1.1 Identity

Every durable domain object has a stable identity assigned by the component that owns its lifecycle.

Identities must be:

- unique within their domain;
- immutable;
- opaque to callers;
- safe to use as references in events;
- independent of display names and storage locations.

Callers must not infer authority from possession of an identity.

### 1.2 Ownership

Each contract identifies one authoritative owner.

The owner is responsible for:

- validating creation;
- enforcing invariants;
- applying legal state transitions;
- emitting lifecycle events;
- persisting current state where required.

Other components may propose changes but may not mutate the object directly.

### 1.3 Immutability

Objects are either:

- **immutable records**, replaced by new versions when changed; or
- **stateful aggregates**, changed only through validated transitions.

Repository evidence, events, artifact content, model requests, model responses, tool calls, tool results, and validation reports are immutable after creation.

Run state, task state, context state, budget state, repository-session state, and workspace state are stateful aggregates.

### 1.4 Version binding

Any contract that describes repository content must identify the repository version and, where mutable workspace state is involved, the workspace version from which it was derived.

Version-bound objects may not silently migrate to a later version.

### 1.5 Scope

Contracts that grant access or address repository data must carry or inherit a runtime-controlled scope.

Scope may include:

- installation;
- tenant;
- workspace;
- repository;
- repository version;
- workspace version;
- run;
- validation execution.

Caller-supplied identifiers do not override the established scope.

### 1.6 Artifact references

Large content is represented by an `ArtifactReference` rather than embedded in first-class event or state records.

The runtime may inline small values for convenience, but the semantic source of truth for an artifact is its immutable stored content and content hash.

### 1.7 Causation and correlation

Operations and events should identify:

- the operation that directly caused them;
- the larger workflow or turn to which they belong.

This allows a model request, tool call, budget reservation, and resulting context changes to be reconstructed as one causal chain.

### 1.8 Error contracts

Errors that cross component or protocol boundaries must preserve a stable Kiln error object.

A transport may wrap the error in its own envelope. For JSON-RPC transports, the stable Kiln error object is carried under `error.data.kiln_error`. Other transports must preserve the same semantic object even if the envelope differs.

#### Stable shape

A Kiln error contains:

```json
{
  "code": "runtime.unsupported_protocol_version",
  "category": "compatibility",
  "message": "Unsupported runtime protocol version",
  "retryable": false,
  "details": {},
  "correlation_id": "corr_...",
  "runtime_id": "runtime_..."
}
```

Required fields:

| Field | Meaning |
| --- | --- |
| `code` | Stable dotted Kiln error code. Clients may branch on this value. |
| `category` | Stable coarse error category. |
| `message` | Human-readable diagnostic message. Not for branching. |
| `retryable` | Whether retrying the same operation may succeed without changing inputs. |
| `details` | Error-specific structured details. Empty when no structured details exist. |

Optional fields:

| Field | Meaning |
| --- | --- |
| `correlation_id` | Request, operation, or workflow correlation identity, when available. |
| `runtime_id` | Runtime session identity, when available. |
| `run_id` | Run identity, when the error belongs to a run. |
| `operation_id` | Operation identity, when the error belongs to a tracked operation. |

#### Categories

Stable error categories are:

| Category | Meaning |
| --- | --- |
| `compatibility` | Version, schema-set, or compatibility negotiation failed. |
| `validation` | Caller input, method params, or returned data failed validation. |
| `lifecycle` | Operation is not legal in the current object or session state. |
| `authorization` | Requested authority was not granted. |
| `budget` | Budget reservation, commitment, deadline, or exhaustion failed. |
| `not_found` | Referenced object does not exist in the caller's scope. |
| `conflict` | Request conflicts with a current version, state, or concurrent operation. |
| `shutdown` | Component is draining, shutting down, or already shut down. |
| `internal` | Component failed unexpectedly. |

#### Code ownership

Error-code prefixes identify the domain that owns the error semantics.

Initial prefixes:

| Prefix | Owner |
| --- | --- |
| `runtime.` | Runtime process/session protocol. |
| `run.` | Run coordinator and run lifecycle. |
| `repository.` | Repository session manager and repository worker protocol. |
| `model.` | Model gateway and model adapter boundary. |
| `capability.` | Capability broker and authorization decisions. |
| `budget.` | Budget manager. |
| `artifact.` | Artifact storage and integrity checks. |
| `validation.` | Validation package and validation execution. |

A component must not reuse another component's prefix for different semantics.

#### Stability rules

The required Kiln error fields are compatibility-stable.

Implementations may add new `details` keys, but they must not remove or rename required fields without a compatibility-major change.

Clients may branch on `code`, `category`, and `retryable`. Clients must not branch on `message`.

The `details` object is intentionally error-specific. Clients must not require unknown detail keys unless they are documented for a specific error code.

Components should preserve the full Kiln error object when converting errors into language-native exceptions, persisted events, health diagnostics, or protocol responses.

---

## 2. Identity and scope contracts

### 2.1 Installation

#### Meaning

Represents one local Kiln installation and its canonical embedded database.

#### Owner

Python SDK and runtime process supervisor.

#### Contains

- installation identity;
- database location;
- runtime version;
- schema version;
- installation-level configuration;
- creation and migration metadata.

#### Invariants

- One local installation has one canonical database by default.
- Alternate database locations may be explicitly configured.
- An installation identity does not imply access to every repository or run stored in the database.

---

### 2.2 Workspace

#### Meaning

Represents a registered working environment containing one or more repositories or repository snapshots.

A workspace is a durable organizational and security boundary. It is not the same as a particular filesystem state.

#### Owner

Runtime persistence layer.

#### Created from

- a local root path;
- a mounted workspace;
- a hosted snapshot location;
- a restored workspace identity.

#### Contains

- workspace identity;
- installation or tenant scope;
- canonical root or snapshot identity;
- display name;
- registered repositories;
- creation metadata;
- active or archived status.

#### Invariants

- The workspace identity is stable if its local root moves.
- A workspace does not itself grant filesystem access.
- Repository and run access must remain scoped beneath the workspace.

---

### 2.3 Repository

#### Meaning

Represents a logical source-code repository across revisions and mutable workspace states.

#### Owner

Repository session manager.

#### Contains

- repository identity;
- workspace identity;
- canonical source identity where known;
- display name;
- repository kind;
- metadata required to resolve revisions.

#### Invariants

- A repository is not a revision.
- Multiple repository versions may belong to one repository.
- A repository identity does not expose source content without an authorized repository session.

---

### 2.4 RepositoryVersion

#### Meaning

Represents one immutable source baseline or logically immutable indexed repository state.

Examples include:

- a pinned Git commit;
- an imported source snapshot;
- a derived checkpoint created from a workspace version.

#### Owner

Repository session manager and persistence layer.

#### Contains

- repository-version identity;
- repository identity;
- source revision or snapshot identity;
- parent repository version, when derived;
- content digest;
- index compatibility metadata;
- creation reason;
- preparation status;
- creation timestamp.

#### Lifecycle

```text
registered
  → preparing
  → ready
  → superseded | invalid | failed
```

#### Invariants

- Its source identity and content digest never change after it becomes ready.
- All indexed evidence derived from it carries its identity.
- A failed or invalid version cannot open a current repository session.
- The mutable current index may materialize only one active state for a repository at a time, but the version journal preserves how that state was reached.

---

### 2.5 WorkspaceVersion

#### Meaning

Represents one ordered state of a mutable task workspace.

The current index is mutable, while the workspace-version journal records each logical transition.

#### Owner

Workspace manager.

#### Contains

- workspace-version identity;
- repository identity;
- base repository version;
- parent workspace version;
- ordered mutation set;
- affected paths;
- invalidated evidence set or invalidation reference;
- synchronization status;
- creation timestamp.

#### Lifecycle

```text
created
  → index_stale
  → synchronizing
  → synchronized
  → superseded
```

A version with no index-affecting mutations may move directly from `created` to `synchronized`.

#### Invariants

- Workspace versions are monotonically ordered within a mutable workspace lineage.
- A mutation creates a new workspace version.
- A workspace mutation and its invalidation record are committed atomically.
- `synchronized` means all evidence required for current queries matches that workspace version.
- Historical workspace versions need not remain fully queryable in the first implementation.

---

### 2.6 RepositorySession

#### Meaning

Represents an authorized, scoped channel for querying one repository state.

#### Owner

Repository session manager.

#### Contains

- repository-session identity;
- run identity;
- repository identity;
- repository version;
- workspace version;
- allowed repository operations;
- creation time;
- expiry or close state;
- worker-session binding.

#### Lifecycle

```text
opening
  → open
  → refreshing
  → open
  → closing
  → closed
```

An unrecoverable worker or version error may transition the session to `failed`.

#### Invariants

- All repository requests inherit the session scope.
- Callers cannot substitute arbitrary repository or version identities on individual queries.
- The session rejects evidence that does not match its repository and workspace versions.
- A closed or failed session cannot perform operations.
- Session possession does not imply filesystem-write or process-execution authority.

---

## 3. Run contracts

### 3.1 RunSpecification

#### Meaning

Declares the requested Kiln execution before runtime state exists.

#### Owner

Product interface creates it; run coordinator validates and accepts it.

#### Contains

- repository reference;
- task specification;
- model configuration;
- context-policy selection and configuration;
- budget limits;
- security profile;
- validation specification;
- requested output mode;
- caller metadata;
- optional idempotency key.

#### Creation requirements

The run coordinator must reject a specification when:

- the repository reference cannot be scoped;
- budgets are malformed or exceed installation policy;
- the requested model is unavailable;
- the requested policy is unavailable;
- requested capabilities exceed the security profile;
- validation requirements are inconsistent;
- the specification version is unsupported.

#### Invariants

- A `RunSpecification` is immutable after acceptance.
- Defaults are resolved before the run enters `created`.
- Secrets are represented by controlled references, not raw values.
- Requested permissions are not equivalent to granted capabilities.

---

### 3.2 TaskSpecification

#### Meaning

Represents the user's requested software-engineering objective and its trusted constraints.

#### Owner

Product interface creates it; run coordinator freezes it.

#### Contains

- task description;
- success criteria;
- explicit constraints;
- optional target paths or symbols;
- optional issue or workflow references;
- requested deliverables;
- trusted instruction provenance.

#### Invariants

- Repository content cannot modify the task specification.
- Model-generated plans do not become trusted task constraints.
- Trusted constraints remain pinned in model context or otherwise enforced by the runtime.

---

### 3.3 Run

#### Meaning

Represents one accepted execution of a `RunSpecification`.

#### Owner

Run coordinator.

#### Contains

- run identity;
- accepted specification;
- lifecycle status;
- task state;
- repository session;
- current workspace version;
- budget state;
- capability grants;
- context state;
- pending operation;
- validation state;
- terminal result reference.

#### Lifecycle

```text
created
  → initializing
  → preparing_repository
  → running
  → producing_output
  → validating
  → completed
```

From any non-terminal state, the run may transition to:

- `failed`;
- `cancelled`;
- `exhausted`.

#### Recoverability

Only these interrupted states are recoverable initially:

- `preparing_repository`;
- `validating`.

An interrupted `running`, `initializing`, or `producing_output` run becomes `failed` with a runtime-interruption reason.

#### Invariants

- A run has exactly one accepted specification.
- A run has exactly one terminal state.
- A terminal run has exactly one primary stop reason.
- State transitions are validated and emit events.
- The current state can be derived from persisted state plus committed events.
- The run never directly owns publication credentials.

---

### 3.4 RunState

#### Meaning

Represents the current materialized state of a run.

#### Owner

Run coordinator.

#### Contains

- lifecycle state;
- current turn;
- current task state;
- active repository session;
- active workspace version;
- current context ledger summary;
- budget summary;
- active capability-grant references;
- pending operation reference;
- last committed event sequence;
- recovery metadata;
- terminal result reference when terminal.

#### Invariants

- There is at most one current `RunState` per run.
- It is updated only after the corresponding event and required artifacts are durably committed.
- A pending operation identifies whether replay, retry, or failure is legal.
- It does not embed large payloads.

---

### 3.5 TaskState

#### Meaning

Represents the runtime's structured view of task progress.

#### Owner

Task state manager.

#### Contains

- current objective;
- current plan;
- completed steps;
- unresolved questions;
- hypotheses;
- proposed changes;
- known failures;
- completion evidence;
- state revision.

#### Invariants

- Task state is runtime-authored, not model-authored.
- Model outputs may propose updates, but the runtime validates and records them.
- Task state changes are traceable to operations and events.

---

### 3.6 Operation

#### Meaning

Represents one bounded unit of work performed by or through the runtime.

Examples:

- repository search;
- source retrieval;
- graph expansion;
- model invocation;
- context rendering;
- validation step;
- artifact creation.

#### Owner

The component that initiates the operation, usually the runtime coordinator or agent loop.

#### Contains

- operation identity;
- operation kind;
- run identity;
- parent operation or turn identity;
- lifecycle status;
- deadline;
- capability reference;
- budget reservation reference;
- input reference;
- output reference;
- error reference.

#### Lifecycle

```text
planned
  → reserved
  → running
  → succeeded | failed | cancelled | denied | exhausted
```

#### Invariants

- Budgeted operations reserve budget before execution.
- Capability-guarded operations cite a grant or denial.
- Operation results are immutable once committed.
- An operation does not change top-level run state directly.

---

## 4. Context contracts

### 4.1 ContextItem

#### Meaning

Represents a unit of information that may be available to, admitted into, evicted from, or observed by the model context.

A context item is not necessarily prompt text. It may be:

- source code;
- a symbol outline;
- a repository search result;
- a graph edge set;
- a task-state summary;
- a validation report;
- a prior model observation;
- a rendered message segment reference.

#### Owner

Context manager.

#### Contains

- context-item identity;
- semantic kind;
- trust level;
- source object reference;
- repository/workspace version binding where applicable;
- artifact reference for large content;
- estimated token cost;
- provenance;
- observation status;
- eviction status.

#### Invariants

- Repository-derived items carry repository and workspace version identities.
- Untrusted content is never merged into trusted instruction fields.
- Availability does not imply admission to active context.
- Admission decisions are recorded.
- Eviction preserves auditability.

---

### 4.2 ContextPlan

#### Meaning

Represents a proposed change to active model context.

#### Owner

Context policy proposes it; context manager validates and applies it.

#### Contains

- plan identity;
- triggering operation;
- candidate items;
- proposed admissions;
- proposed evictions;
- rejected candidates;
- estimated active token total;
- policy rationale or rule trace.

#### Invariants

- A context plan is a proposal until applied.
- Applying a plan must not exceed configured context limits.
- The runtime may reject a policy proposal that violates trust, version, or budget rules.
- A plan does not directly invoke the model.

---

### 4.3 ContextLedger

#### Meaning

Records what information was available, admitted, rendered, observed by the model, or evicted over the run.

#### Owner

Context manager.

#### Contains

- run identity;
- active context revisions;
- context-item references;
- admission and eviction events;
- rendered request references;
- model observation markers;
- final context summary.

#### Invariants

- It is reconstructable from context events and artifacts.
- It records model-visible context, not just selected candidates.
- It preserves trust boundaries.
- It supports replay and audit.

---

## 5. Repository evidence contracts

### 5.1 RepositoryCandidate

#### Meaning

Represents structured evidence returned by repository retrieval.

A repository candidate is evidence available to the runtime. It is not automatically admitted into model context.

#### Owner

Repository engine produces it; runtime validates and stores or references it.

#### Contains

- candidate identity;
- repository-session identity;
- repository identity;
- repository version;
- workspace version;
- evidence kind;
- source location;
- symbol identity where applicable;
- content or artifact reference;
- representation kind;
- estimated token cost;
- match or relation metadata;
- completeness flag;
- confidence or derivation metadata.

#### Invariants

- It must match the repository session scope.
- It must not claim a different repository, repository version, or workspace version than the session permits.
- It must identify whether content is full source, excerpt, outline, summary, or graph evidence.
- It is untrusted content for prompt construction.
- It may become unavailable if the session closes, but its persisted reference remains auditable.

---

### 5.2 SourceLocation

#### Meaning

Identifies a precise location in repository content.

#### Owner

Repository engine.

#### Contains

- repository identity;
- repository version;
- workspace version;
- repository-relative path;
- optional symbol identity;
- optional byte range;
- optional line range;
- encoding or normalization metadata.

#### Invariants

- Paths are repository-relative and normalized.
- Locations cannot escape the repository scope.
- Line ranges are display aids; byte ranges or content hashes are authoritative where exact replay matters.

---

## 6. Model contracts

### 6.1 ModelRequest

#### Meaning

Represents one provider-neutral request to a model.

#### Owner

Model gateway.

#### Contains

- request identity;
- run identity;
- turn identity;
- model configuration reference;
- rendered messages or artifact references;
- tool definitions;
- generation parameters;
- input-token estimate;
- output-token reservation;
- egress decision reference;
- provenance mapping.

#### Invariants

- A request is immutable once sent.
- It references exactly what was rendered for the model.
- It has already passed egress control.
- It does not embed unapproved secrets or excluded content.

---

### 6.2 ModelResponse

#### Meaning

Represents one normalized response from a model provider.

#### Owner

Model gateway.

#### Contains

- response identity;
- request identity;
- provider response reference;
- normalized message content;
- tool-call or proposal data;
- stop reason;
- token usage;
- safety or refusal metadata where applicable;
- raw-response artifact reference when retained.

#### Invariants

- A model response is untrusted until interpreted by the runtime.
- Token usage is reported to the budget manager.
- Tool calls are proposals, not effects.
- The raw provider response may be artifact-backed.

---

### 6.3 ModelProposal

#### Meaning

Represents a model-suggested action after response interpretation.

Examples:

- retrieve more repository evidence;
- continue reasoning;
- produce final answer;
- request validation;
- declare inability to proceed.

#### Owner

Agent loop or model-response interpreter.

#### Contains

- proposal identity;
- source response identity;
- proposal kind;
- structured arguments;
- confidence or rationale where available;
- validation status.

#### Invariants

- A proposal has no effect until accepted by the runtime.
- Unsupported proposal kinds are rejected.
- Accepted proposals create explicit operations or lifecycle transitions.

---

## 7. Budget contracts

### 7.1 BudgetState

#### Meaning

Represents current limits, reservations, commitments, and exhaustion state for a run.

#### Owner

Budget manager.

#### Contains

- run identity;
- configured limits;
- current committed usage;
- active reservations;
- exhausted domains;
- reconciliation metadata;
- update sequence.

#### Invariants

- Usage cannot exceed hard limits after commit.
- A budgeted operation must reserve before execution.
- Reservations either commit or release.
- Exhaustion is explicit and names the exhausted domain.

---

### 7.2 BudgetReservation

#### Meaning

Represents a temporary hold against one or more budget domains before an operation executes.

#### Owner

Budget manager.

#### Contains

- reservation identity;
- run identity;
- operation identity;
- budget domain;
- estimated amount;
- expiry;
- status.

#### Lifecycle

```text
reserved
  → committed | released | expired | denied
```

#### Invariants

- Reservations are bounded by amount and expiry.
- A committed reservation records actual usage.
- Expired reservations cannot commit.
- Denied reservations prevent the associated operation from executing.

---

## 8. Capability contracts

### 8.1 CapabilityGrant

#### Meaning

Represents explicit runtime authority to perform a class of operation within a scope.

Capabilities are not user-facing permissions. They are runtime-internal execution authorities derived from security profile, policy, and current state.

#### Owner

Capability broker.

#### Contains

- grant identity;
- subject component;
- operation kind;
- scope;
- constraints;
- expiry or revocation state;
- derivation reason.

#### Invariants

- Possessing an object identity is not a capability.
- Grants are scoped and least-privilege.
- Grants cannot be expanded by the subject that receives them.
- Capability checks are recorded for sensitive operations.

---

### 8.2 CapabilityDecision

#### Meaning

Represents the result of checking whether an operation is authorized.

#### Owner

Capability broker.

#### Contains

- decision identity;
- requested operation;
- requested scope;
- subject;
- allowed or denied outcome;
- grant reference when allowed;
- denial reason when denied;
- policy trace.

#### Invariants

- Every sensitive operation has a decision.
- Denied decisions do not create grants.
- Decisions are immutable audit records.

---

## 9. Event contracts

### 9.1 Event

#### Meaning

Represents one immutable fact that occurred in Kiln.

Events are audit and replay records. They are not commands.

#### Owner

Component that commits the fact; persistence layer stores it.

#### Contains

- event identity;
- event kind;
- timestamp;
- sequence within stream;
- scope;
- subject reference;
- causal operation;
- correlation identity;
- payload reference or payload;
- schema version.

#### Invariants

- Events are append-only.
- Event ordering is stable within a stream.
- Events do not contain large unbounded payloads inline.
- State changes that require events commit atomically with the event.

---

### 9.2 EventStream

#### Meaning

Represents an ordered sequence of events for a scope.

Common streams:

- installation stream;
- workspace stream;
- repository stream;
- run stream;
- validation stream.

#### Owner

Persistence layer.

#### Contains

- stream identity;
- stream scope;
- ordered event sequence;
- high-water mark;
- retention policy.

#### Invariants

- Events have a total order within their stream.
- Cross-stream ordering requires causal or correlation references.
- Consumers may resume from a known sequence.

---

## 10. Artifact contracts

### 10.1 ArtifactReference

#### Meaning

Identifies immutable stored content.

#### Owner

Artifact store.

#### Contains

- artifact identity;
- content kind;
- storage backend reference;
- byte length;
- content hash;
- encoding;
- schema version where applicable;
- creation metadata.

#### Invariants

- Artifact content is immutable.
- Content hash verifies integrity.
- Artifact references do not imply read authority outside their scope.
- Artifacts may be garbage-collected only according to retention policy and with preserved audit semantics.

---

## 11. Validation contracts

### 11.1 ValidationRequest

#### Meaning

Represents a request to validate a proposed output or workspace state.

#### Owner

Runtime creates it; validation package executes it.

#### Contains

- validation identity;
- run identity;
- workspace version;
- validation profile;
- required checks;
- budget or timeout constraints;
- input artifact references.

#### Invariants

- Validation runs against an explicit workspace version.
- Validation does not mutate the run result directly.
- Validation result is evidence for a lifecycle transition.

---

### 11.2 ValidationResult

#### Meaning

Represents immutable validation evidence.

#### Owner

Validation package.

#### Contains

- validation identity;
- status;
- check results;
- diagnostics;
- produced artifacts;
- started and completed timestamps.

#### Invariants

- It references exactly what was validated.
- It does not itself change run state.
- The run coordinator decides lifecycle transitions based on validation result.

---

## 12. Terminal result contracts

### 12.1 RunResult

#### Meaning

Represents the final public result of a run.

#### Owner

Run coordinator.

#### Contains

- run identity;
- terminal status;
- stop reason;
- final answer or output reference;
- usage summary;
- context ledger reference;
- event stream bounds;
- artifact references;
- validation summary where applicable;
- replay completeness classification.

#### Invariants

- There is exactly one `RunResult` per terminal run.
- It references the final committed run state.
- It does not expose restricted artifacts without authorization.
- It preserves enough references for audit and replay.

---

## 13. Deferred contracts

The following contracts are intentionally deferred from the first vertical slice:

- workspace mutation;
- patch representation;
- command execution;
- test execution;
- publication;
- hosted task ingress;
- hosted runner lease;
- external integration credentials;
- learned policy state.

Deferred contracts must not be smuggled into first-slice objects as unstructured blobs.

Where a deferred capability is needed later, it should receive its own explicit contract with:

- owner;
- scope;
- lifecycle;
- invariants;
- event expectations;
- artifact semantics.

---

## 14. First-slice contract boundary

The first implementation slice should exercise:

- installation;
- workspace;
- repository;
- repository version;
- workspace version;
- repository session;
- run specification;
- run;
- run state;
- task state;
- operation;
- context item;
- context plan;
- context ledger;
- repository candidate;
- model request;
- model response;
- model proposal;
- budget state;
- budget reservation;
- capability grant;
- capability decision;
- event;
- artifact reference;
- run result.

It should not exercise:

- mutable workspace editing;
- patches;
- command execution;
- publication.

The deferred contracts should still remain semantically stable enough that later features do not require redefining the first-slice objects.