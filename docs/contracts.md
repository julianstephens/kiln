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

- Task state is distinct from the raw conversation transcript.
- Model output may propose updates, but the runtime validates and commits them.
- Task state must not override trusted constraints in `TaskSpecification`.
- Historical revisions may be referenced for replay.

---

### 3.6 StopReason

#### Meaning

Explains why a run entered a terminal state.

#### Owner

Stop controller.

#### Categories

- success;
- budget exhausted;
- cancelled;
- policy denied;
- model failed;
- repository failed;
- tool failed;
- validation failed;
- runtime interrupted;
- internal error.

#### Contains

- stable reason code;
- terminal class;
- human-readable summary;
- responsible component;
- causal event reference;
- retryability classification;
- optional diagnostic artifact reference.

#### Invariants

- Exactly one primary stop reason is assigned.
- Additional diagnostics do not replace the primary reason.
- A model-proposed completion does not itself create a success reason.

---

### 3.7 RunResult

#### Meaning

Represents the final externally consumable outcome of a run.

#### Owner

Run coordinator.

#### Contains

- run identity;
- terminal status;
- primary stop reason;
- final answer artifact or inline value;
- patch artifact when produced;
- changed-file manifest reference;
- validation-report reference when validation ran;
- usage summary;
- event-stream range or reference;
- context-ledger reference;
- additional artifact references.

#### Invariants

- Created only after the run is terminal.
- Immutable after creation.
- Does not imply publication occurred.
- A successful result requiring validation cannot be publication-eligible without a passing validation report.

---

## 4. Repository evidence contracts

### 4.1 RepositoryRequest

#### Meaning

Represents one typed request to the repository engine through an open `RepositorySession`.

#### Owner

Runtime repository adapter.

#### Kinds

- prepare;
- search;
- get source;
- get file;
- expand graph;
- find callers;
- find callees;
- get summary;
- get representation;
- invalidate;
- refresh.

#### Contains

- request identity;
- repository-session identity;
- operation kind;
- structured parameters;
- result limits;
- budget reservation reference;
- causation and correlation identities.

#### Invariants

- The session, not caller-supplied parameters, determines repository scope.
- Request size and result limits are bounded.
- Unknown operation kinds fail closed.
- Every accepted request produces one terminal response or cancellation result.

---

### 4.2 RepositoryCandidate

#### Meaning

Represents one structured piece of repository evidence available for policy evaluation.

#### Owner

Repository engine creates it; runtime validates it.

#### Contains

- content identity;
- repository identity;
- repository version;
- workspace version;
- semantic kind;
- source location;
- qualified name where applicable;
- representation kind;
- content or artifact reference;
- estimated token cost;
- relevance metadata;
- graph metadata;
- alternative representations;
- provenance;
- freshness status.

#### Semantic kinds

Examples include:

- file;
- symbol;
- signature;
- source range;
- repository summary;
- package summary;
- file summary;
- graph path;
- search match;
- diagnostic.

#### Representation kinds

Examples include:

- full source;
- filtered source;
- signature;
- summary;
- outline;
- search snippet;
- relation list;
- hierarchical summary.

#### Freshness states

- current;
- stale;
- historical;
- unknown.

#### Invariants

- Content identity is stable for the represented repository fact and version.
- Candidate token cost is advisory.
- `current` means it matches the active repository and workspace versions.
- Stale candidates cannot be admitted as current context.
- Historical candidates must be explicitly labeled when shown to a model.
- Candidate provenance identifies how the evidence was derived.
- Alternative representations refer to the same underlying content identity or explicitly declare their relationship.

---

### 4.3 Provenance

#### Meaning

Explains where a piece of evidence or output came from and how it was derived.

#### Owner

The component creating the evidence or artifact.

#### Contains

- source object identities;
- repository and workspace versions;
- producing operation;
- transformation or representation kind;
- producer version;
- creation time;
- content hash;
- optional confidence information.

#### Invariants

- Provenance is immutable.
- Derived evidence references its source evidence or source location.
- Provenance never grants authority.

---

### 4.4 InvalidationRecord

#### Meaning

Records which repository evidence became stale because of a workspace mutation or configuration change.

#### Owner

Repository consistency manager.

#### Contains

- invalidation identity;
- prior and new workspace versions;
- mutation references;
- affected files;
- affected content identities where known;
- affected relation classes;
- reason;
- creation time;
- refresh status.

#### Invariants

- Created atomically with the workspace-version transition.
- It may conservatively invalidate more evidence than strictly necessary.
- Evidence identified by an unresolved invalidation cannot be treated as current.

---

### 4.5 RefreshRequest

#### Meaning

Requests synchronization of the mutable current index with a workspace version.

#### Owner

Repository consistency manager.

#### Contains

- refresh identity;
- repository session;
- target workspace version;
- refresh mode;
- affected paths or invalidation references;
- completion requirements;
- budget reservation.

#### Modes

- eager incremental;
- lazy incremental;
- batched incremental;
- full rebuild.

#### Invariants

- The runtime selects or approves the refresh mode.
- A completed refresh identifies the workspace version to which the index is synchronized.
- Full rebuild is required when incremental correctness cannot be guaranteed.

---

## 5. Context contracts

### 5.1 ContextItem

#### Meaning

Represents one piece of information tracked by the runtime for possible or actual model use.

#### Owner

Context manager.

#### Contains

- context-item identity;
- source type;
- source object identity;
- repository and workspace versions when applicable;
- active representation;
- lifecycle state;
- estimated token cost;
- first-seen turn;
- last-used turn;
- admission reason;
- pin status;
- provenance;
- replacement or compression relationship.

#### Lifecycle states

- available;
- active;
- observed;
- compressed;
- evicted;
- rejected;
- stale.

`pinned` is an attribute, not a lifecycle state.

#### Invariants

- One context item has one active representation at a time.
- A stale item cannot become active as current evidence without refresh or historical labeling.
- Activation, eviction, compression, and replacement are runtime-controlled transitions.
- Observed means the item appeared in at least one committed model request.
- Eviction does not delete provenance or history.

---

### 5.2 ContextState

#### Meaning

Represents the current context ledger for a run.

#### Owner

Context manager.

#### Contains

- pinned item identities;
- available item identities;
- active item identities and ordering;
- observed item identities;
- stale item identities;
- current token estimate;
- model-context limit;
- context-state revision.

#### Invariants

- Active items are a subset of valid, non-stale items unless explicitly historical.
- Pinned instructions cannot be evicted by ordinary policy actions.
- The active ordering used by the renderer is deterministic for a committed state.
- Context state changes emit events.

---

### 5.3 ContextPlan

#### Meaning

Represents a policy's proposed context and retrieval actions for one planning step.

#### Owner

Context policy creates it; runtime validates and applies it.

#### Contains

- plan identity;
- run and turn identities;
- input context-state revision;
- proposed actions;
- rationale metadata;
- estimated budget impact;
- policy identity and version.

#### Actions

- retrieve;
- admit;
- reject;
- compress;
- replace;
- evict;
- preserve;
- pin;
- defer.

#### Invariants

- A plan is declarative and has no direct side effects.
- Retrieval actions are proposals; the runtime performs repository operations.
- The runtime rejects plans based on stale input state.
- The runtime rejects actions that exceed authority, budget, or version rules.
- Applying a plan produces a distinct committed context-state revision.

---

### 5.4 RenderedContext

#### Meaning

Represents the exact provider-neutral content prepared for one model invocation.

#### Owner

Context renderer.

#### Contains

- rendering identity;
- run and turn identities;
- ordered messages or blocks;
- tool definitions;
- included context-item identities;
- content-to-provenance mapping;
- estimated token count;
- rendering rules and version;
- artifact reference for full rendered content when stored externally.

#### Invariants

- Immutable after creation.
- Completely determines what is submitted to the model gateway, subject only to authorized egress redaction.
- Included repository evidence identifies its trust class and provenance.
- The full rendered form is recoverable for audit when retention policy permits.

---

## 6. Budget contracts

### 6.1 BudgetLimits

#### Meaning

Declares maximum resource consumption for a run or sub-operation.

#### Owner

Run coordinator establishes it from the accepted specification and installation policy.

#### Domains

- model input tokens;
- model output tokens;
- model calls;
- tool calls;
- repository requests;
- elapsed wall time;
- monetary cost;
- command time;
- command output size;
- artifact size;
- context churn or repeated-token cost.

#### Invariants

- Limits are immutable after run creation unless a trusted authority explicitly grants an increase.
- A child-operation budget cannot exceed its parent budget.
- Missing domains use explicit unlimited or disabled semantics; absence is not ambiguous.

---

### 6.2 BudgetState

#### Meaning

Represents current reserved, committed, and remaining usage.

#### Owner

Budget manager.

#### Contains

For each budget domain:

- configured limit;
- reserved amount;
- committed amount;
- remaining amount;
- exhaustion status.

It also contains:

- state revision;
- latest transaction sequence;
- estimate-versus-actual metrics.

#### Invariants

- Reserved plus committed usage cannot exceed a hard limit.
- Remaining usage is derived, not independently assigned.
- Budget state changes occur through transactions.
- Provider-reported actual usage is reconciled even when it exceeds an estimate.

---

### 6.3 BudgetReservation

#### Meaning

Temporarily allocates resources before an operation begins.

#### Owner

Budget manager.

#### Contains

- reservation identity;
- run identity;
- operation identity;
- budget domains and amounts;
- creation time;
- expiry;
- status;
- estimate source.

#### Lifecycle

```text
proposed
  → reserved
  → committed | released | expired
```

#### Invariants

- An operation requiring budget cannot begin without an active reservation.
- A reservation is bound to one operation.
- Commit records actual usage and releases any unused amount.
- Failed operations still commit resources actually consumed.

---

### 6.4 BudgetTransaction

#### Meaning

Records an immutable change to budget state.

#### Owner

Budget manager.

#### Kinds

- reserve;
- commit;
- release;
- expire;
- adjust by trusted authority;
- reconcile actual usage.

#### Contains

- transaction identity;
- reservation identity where applicable;
- domain amounts;
- before and after state revisions;
- causal operation;
- timestamp;
- reason.

#### Invariants

- Transactions are append-only.
- Reconciliation never rewrites earlier estimates.
- Estimation error remains observable.

---

## 7. Capability and tool contracts

### 7.1 SecurityProfile

#### Meaning

Defines the maximum authority a run may receive.

#### Owner

Trusted product or installation configuration.

#### Contains

- filesystem-read scopes;
- filesystem-write scopes;
- process-execution rules;
- network rules;
- model-egress rules;
- external-integration rules;
- artifact and validation rules;
- approval requirements;
- default-deny settings.

#### Invariants

- The model cannot modify the security profile.
- A run specification may request less authority but cannot expand the profile.
- Defaults deny authority not explicitly granted.

---

### 7.2 CapabilityScope

#### Meaning

Represents the bounded set of resources and operations to which a capability rule, grant, request, or decision applies.

A capability scope identifies where authority may be exercised. It does not itself grant authority.

#### Owner

The component that establishes the enclosing security profile, capability grant, or capability decision.

The capability broker validates and resolves scopes before they become effective.

#### Contains

A scope may constrain authority by:

- installation identity;
- tenant identity;
- workspace identity;
- repository identity;
- repository version;
- workspace version;
- run identity;
- repository-session identity;
- artifact identity or artifact class;
- filesystem roots or path patterns;
- network destinations;
- external-integration identities;
- model providers or model identities;
- validation execution;
- operation kinds.

A scope may also contain:

- explicit exclusions;
- depth or traversal limits;
- read, write, execute, or egress restrictions;
- validity bounds inherited from the enclosing grant;
- scope version or normalization metadata.

#### Composition

Scopes may be narrowed through intersection.

For example:

- a security profile may permit repository reads within a workspace;
- a run may request access to one repository;
- a repository session may bind access to one repository version;
- the effective grant scope is the intersection of those constraints.

A child scope cannot expand its parent scope.

#### Invariants

- A scope is descriptive and does not independently authorize an operation.
- Effective authority requires both an applicable `CapabilityGrant` and a matching scope.
- Missing scope dimensions do not imply unrestricted access.
- Caller-supplied identities cannot expand the runtime-established scope.
- Scope narrowing is explicit and inspectable.
- Scope comparison and intersection are deterministic.
- Resource identities are treated as opaque values.
- Repository evidence must remain bound to the repository and workspace versions in its effective scope.
- A scope attached to an immutable grant or decision is immutable.

---

### 7.3 CapabilityGrant

#### Meaning

Represents runtime authorization to perform a category of operation within a specific scope.

#### Owner

Capability broker.

#### Contains

- grant identity;
- capability type;
- run identity;
- resource scope;
- allowed operation constraints;
- creation source;
- approval metadata;
- start and expiry times;
- revocation state.

#### Invariants

- Grants are explicit, scoped, revocable, and non-transitive.
- Possession of one grant does not imply another.
- Grants cannot exceed the security profile.
- Every effectful operation identifies the grant under which it was authorized.

---

### 7.4 CapabilityDecision

#### Meaning

Represents the broker's immutable authorization decision for one requested operation.

#### Owner

Capability broker.

#### Outcomes

- allowed;
- denied;
- narrowed;
- approval required.

#### Contains

- decision identity;
- request identity;
- applicable grant identities;
- outcome;
- effective scope;
- reason code;
- approval reference;
- timestamp.

#### Invariants

- Every effectful operation has exactly one terminal capability decision.
- Denials are recorded and returned as structured results.
- Narrowed authority is explicit and inspectable.

---

### 7.5 ToolDefinition

#### Meaning

Describes an operation the model may propose.

#### Owner

Tool registry.

#### Contains

- tool identity;
- version;
- description;
- argument contract;
- result contract;
- required capabilities;
- side-effect classification;
- timeout and output limits;
- trust classification.

#### Invariants

- Registration does not grant authority.
- Workers cannot introduce unknown runtime operations dynamically.
- Model-visible definitions derive from trusted registered definitions.

---

### 7.6 ToolCall

#### Meaning

Represents one model-proposed invocation of a registered tool.

#### Owner

Agent loop normalizes it; runtime owns execution lifecycle.

#### Contains

- tool-call identity;
- run and turn identities;
- tool identity and version;
- structured arguments;
- requesting model-response identity;
- required capabilities;
- status;
- budget-reservation reference.

#### Lifecycle

```text
proposed
  → validated
  → authorized
  → executing
  → completed | denied | failed | cancelled
```

#### Invariants

- Arguments are schema-validated before authorization.
- A proposed tool call has no side effect.
- Execution requires both budget and capability approval.
- Arbitrary shell strings are not valid command-tool arguments by default.

---

### 7.7 ToolResult

#### Meaning

Represents the immutable outcome of one tool call.

#### Owner

Tool executor and result processor.

#### Contains

- tool-result identity;
- tool-call identity;
- terminal status;
- structured summary;
- diagnostics;
- actual resource usage;
- raw-output artifact references;
- produced context-candidate identities;
- changed-resource references;
- error classification.

#### Invariants

- Raw output does not enter model context directly.
- Result candidates pass through context policy.
- A denied call produces a structured denied result.
- Tool results never grant new capabilities.

---

## 8. Model contracts

### 8.1 ModelConfiguration

#### Meaning

Declares the selected model and invocation constraints.

#### Owner

Run specification selects it; model gateway validates it.

#### Contains

- model identity;
- provider or local adapter identity;
- context limit;
- supported tool-call mode;
- tokenizer or counting strategy;
- generation parameters;
- allowed endpoint;
- credential reference;
- streaming preference.

#### Invariants

- Credentials are referenced, not embedded.
- Configuration cannot bypass egress or budget rules.
- Model capabilities are validated before the first invocation.

---

### 8.2 ModelRequest

#### Meaning

Represents the exact authorized request submitted to a model adapter.

#### Owner

Model gateway.

#### Contains

- model-request identity;
- run and turn identities;
- rendered-context identity;
- model configuration;
- ordered messages;
- tool definitions;
- reserved output limit;
- provider-specific preflight token count;
- budget-reservation reference;
- egress-decision reference;
- full-request artifact reference where required.

#### Invariants

- Immutable after submission.
- Requires approved context, egress decision, and budget reservation.
- Rendered input plus reserved output does not exceed the model context limit.
- Repository content included in the request remains provenance-addressable.

---

### 8.3 EgressDecision

#### Meaning

Represents authorization for data to leave the local execution boundary for model inference.

#### Owner

Model egress controller.

#### Outcomes

- allowed;
- denied;
- redacted;
- approval required.

#### Contains

- decision identity;
- model-request or rendered-context identity;
- provider and endpoint;
- included content identities;
- excluded or redacted content identities;
- byte and token estimates;
- secret-scan result;
- applicable policy;
- reason.

#### Invariants

- Every remote model request has one terminal egress decision.
- Redaction produces a new rendered or request representation rather than mutating history.
- Egress authorization does not grant arbitrary network access.

---

### 8.4 ModelResponse

#### Meaning

Represents the normalized immutable outcome of one model invocation.

#### Owner

Model gateway.

#### Contains

- model-response identity;
- model-request identity;
- generated content or artifact reference;
- proposed tool calls;
- finish reason;
- provider-reported usage;
- latency and provider metadata;
- safety or refusal metadata;
- error classification when applicable.

#### Invariants

- Model output is untrusted.
- Proposed tool calls have no effect until normalized, validated, budgeted, and authorized.
- Provider-reported usage is submitted to the budget manager for reconciliation.
- A response does not directly mutate task, context, workspace, or run state.

---

## 9. Workspace contracts

### 9.1 WorkspaceMutation

#### Meaning

Represents one authorized change to the mutable task workspace.

#### Owner

Workspace manager.

#### Kinds

- create file;
- replace file;
- patch file;
- delete file;
- rename file.

#### Contains

- mutation identity;
- run identity;
- prior workspace version;
- target path;
- operation kind;
- previous content hash where applicable;
- new content or artifact reference;
- capability-decision reference;
- producing tool-call reference;
- timestamp.

#### Invariants

- The target path is resolved within the authorized workspace scope.
- Mutation and new workspace-version creation are atomic.
- The mutation never changes Git remotes or credentials unless a separate explicit capability exists.
- A successful mutation creates invalidation work.

---

### 9.2 ChangedFileManifest

#### Meaning

Represents the normalized set of file changes between the base repository version and a workspace version.

#### Owner

Workspace manager.

#### Contains

- manifest identity;
- base repository version;
- target workspace version;
- ordered changed-file records;
- operation kind per path;
- old and new content hashes;
- summary statistics;
- content hash of the manifest.

#### Invariants

- Immutable after creation.
- Deterministic for the same base and target state.
- Does not itself contain publication authority.

---

### 9.3 PatchArtifact

#### Meaning

Represents a portable change set produced from a base repository version and target workspace version.

#### Owner

Workspace manager.

#### Contains

- artifact reference;
- base repository version;
- target workspace version;
- changed-file-manifest identity;
- patch format;
- content hash;
- generation metadata.

#### Invariants

- Applying it to the declared base either reproduces the intended target changes or fails cleanly.
- Immutable after creation.
- Patch production does not imply validation or publication eligibility.

---

## 10. Event and artifact contracts

### 10.1 Event

#### Meaning

Represents one immutable first-class fact about execution.

#### Owner

The component responsible for the fact creates it; event store sequences it.

#### Contains

- event identity;
- run identity;
- monotonically increasing run sequence;
- timestamp;
- event type;
- schema version;
- structured fact payload;
- artifact references;
- causation identity;
- correlation identity;
- producing component;
- integrity metadata.

#### Event classes

- run lifecycle;
- repository lifecycle;
- workspace mutation;
- context lifecycle;
- budget transaction;
- capability decision;
- model invocation;
- tool invocation;
- validation lifecycle;
- recovery;
- error and retry.

#### Invariants

- Events are append-only.
- Events describe what happened rather than storing full large payloads.
- Sequence is unique and ordered within a run.
- An event is committed before dependent materialized state becomes externally visible.
- Events reference immutable artifacts for large content.

---

### 10.2 ArtifactReference

#### Meaning

Identifies immutable binary or textual content stored as a database blob.

#### Owner

Artifact store.

#### Contains

- artifact identity;
- installation or tenant scope;
- run identity when run-owned;
- artifact kind;
- content type;
- content hash;
- uncompressed size;
- stored size;
- compression method;
- retention class;
- creation time;
- optional encryption metadata.

#### Invariants

- Artifact bytes are immutable.
- Content hash is verified at write and read boundaries.
- Duplicate content may be deduplicated without changing artifact semantics.
- Access is scope-checked; knowing an artifact identity is insufficient.
- Deletion follows retention and reference rules.

---

### 10.3 Artifact

#### Meaning

Represents the actual content identified by an `ArtifactReference`.

#### Owner

Artifact store.

#### Typical kinds

- rendered model request;
- model response;
- repository snapshot;
- source representation;
- patch;
- changed-file manifest;
- command output;
- test output;
- context snapshot;
- validation report;
- final answer;
- provenance bundle.

#### Invariants

- Stored in the installation database as a blob in the initial architecture.
- May be compressed.
- Subject to maximum-size and retention policies.
- The storage abstraction must permit a future non-database backend without changing higher-level contracts.

---

## 11. Validation contracts

### 11.1 ValidationSpecification

#### Meaning

Declares the trusted checks required before a proposed change may be accepted or published.

#### Owner

Trusted run configuration or hosted workflow policy.

#### Contains

- validation profile identity and version;
- patch-application requirements;
- allowed and prohibited paths;
- formatter, linter, type-check, build, and test requirements;
- secret and dependency checks;
- command restrictions;
- resource budgets;
- approval rules;
- publication requirements.

#### Invariants

- Model output cannot weaken it.
- Required checks are explicit and versioned.
- Validation commands are subject to their own capability and sandbox rules.

---

### 11.2 ValidationRequest

#### Meaning

Represents one immutable request to validate a proposed run output in a clean execution boundary.

#### Owner

Run coordinator.

#### Contains

- validation identity;
- run identity;
- base repository version;
- repository-snapshot artifact reference;
- patch-artifact reference;
- changed-file-manifest reference;
- validation specification;
- security profile reference;
- validation budget;
- expected report contract version;
- causation metadata.

#### Lifecycle

```text
created
  → dispatched
  → running
  → completed | failed | cancelled | exhausted
```

An interrupted validation may be redispatched from the immutable request.

#### Invariants

- Persisted before the run commits the transition to `validating`.
- Does not reference the live mutable agent workspace.
- Contains only immutable inputs.
- Does not grant model, publication, or general repository authority.

---

### 11.3 ValidationReport

#### Meaning

Represents the immutable structured outcome of one validation execution.

#### Owner

Validation package.

#### Contains

- validation identity;
- request identity;
- terminal status;
- patch-applicability result;
- observed changed-file manifest;
- policy-check results;
- command and test results;
- security-check results;
- artifact references for detailed output;
- publication-eligibility decision;
- approval requirement;
- failure reasons;
- validator version and environment metadata.

#### Statuses

- passed;
- failed;
- error;
- cancelled;
- exhausted.

#### Invariants

- Immutable after creation.
- `failed` means validation ran and requirements were not met.
- `error` means validation could not reliably determine compliance.
- Publication eligibility is false unless all required checks passed.
- The runtime validates the report's request identity and contract version before accepting it.

---

### 11.4 ValidationExecution

#### Meaning

Represents the recoverable out-of-process execution of one `ValidationRequest`.

#### Owner

Validation package and run coordinator jointly coordinate it; the validation package owns execution internals.

#### Contains

- execution identity;
- validation-request identity;
- worker identity;
- start and completion times;
- execution status;
- budget state;
- report reference;
- retry count;
- recovery metadata.

#### Invariants

- Runs in a clean temporary workspace.
- Materializes the declared base snapshot and applies the declared patch.
- Has no model or publication credentials.
- May be restarted from the immutable request after interruption.
- Temporary workspace is destroyed after terminal completion.

---

## 12. Recovery contracts

### 12.1 RecoveryRecord

#### Meaning

Records a runtime decision to resume or terminate an interrupted run.

#### Owner

Run coordinator.

#### Contains

- recovery identity;
- run identity;
- interrupted lifecycle state;
- last committed event sequence;
- pending-operation identity;
- decision;
- reason;
- resumed operation identity where applicable;
- timestamp.

#### Decisions

- resume repository preparation;
- restart validation;
- fail interrupted run.

#### Invariants

- Only `preparing_repository` and `validating` may resume initially.
- Recovery never assumes an uncommitted side effect completed.
- Resumed operations are idempotent or begin from a verified durable checkpoint.

---

## 13. Cross-contract relationships

```text
Installation
  └── Workspace
        └── Repository
              ├── RepositoryVersion
              └── WorkspaceVersion lineage

RunSpecification
  └── Run
        ├── RunState
        ├── TaskState
        ├── RepositorySession
        ├── ContextState
        │     └── ContextItem
        ├── BudgetState
        │     ├── BudgetReservation
        │     └── BudgetTransaction
        ├── CapabilityGrant
        ├── Event stream
        └── RunResult

RepositorySession
  ├── RepositoryRequest
  └── RepositoryCandidate

ContextPolicy
  └── ContextPlan
        └── ContextState transition

RenderedContext
  └── ModelRequest
        ├── EgressDecision
        ├── BudgetReservation
        └── ModelResponse
              └── ToolCall
                    ├── CapabilityDecision
                    └── ToolResult

WorkspaceMutation
  ├── WorkspaceVersion
  ├── InvalidationRecord
  └── RefreshRequest

RunResult
  ├── PatchArtifact
  ├── ChangedFileManifest
  └── ValidationRequest
        └── ValidationExecution
              └── ValidationReport
```

---

## 14. Contract-level invariants

The following rules apply across all contracts.

1. Model output is always a proposal.
2. Repository and tool results do not enter model context directly.
3. Policies propose retrieval; only the runtime performs it.
4. Every effectful operation has a capability decision.
5. Every resource-consuming operation has an appropriate budget reservation.
6. Every remote model invocation has an egress decision.
7. Every repository-derived object is bound to repository and workspace versions.
8. Every workspace mutation creates a new workspace version and invalidation record.
9. Stale evidence cannot be used as current evidence.
10. Provider-specific token counts govern preflight model reservation.
11. Provider-reported actual usage is reconciled without rewriting estimates.
12. Events contain first-class facts; large content is stored as artifact blobs.
13. Artifact bytes are immutable and content-addressed.
14. Scoped sessions prevent arbitrary cross-repository queries.
15. Logical database scoping is not treated as adversarial tenant isolation.
16. A run has one terminal state and one primary stop reason.
17. Only repository preparation and validation are recoverable initially.
18. Validation consumes immutable inputs in a clean execution boundary.
19. Validation cannot publish, and the agent runtime cannot self-approve publication.
20. Publication credentials never enter the agent or validation execution boundaries.

---

## 15. Initial vertical-slice subset

The first implementation does not need every contract in full.

It must implement the following minimum subset:

- `Installation`;
- `Workspace`;
- `Repository`;
- `RepositoryVersion`;
- `WorkspaceVersion` with an initial synchronized version;
- `RepositorySession`;
- `RunSpecification`;
- `TaskSpecification`;
- `Run`;
- `RunState`;
- `TaskState`;
- `RepositoryRequest`;
- `RepositoryCandidate`;
- `ContextItem`;
- `ContextState`;
- `ContextPlan`;
- `RenderedContext`;
- `BudgetLimits`;
- `BudgetState`;
- `BudgetReservation`;
- `BudgetTransaction`;
- read-only `SecurityProfile`;
- repository-read `CapabilityGrant` and `CapabilityDecision`;
- read-only `ToolDefinition`, `ToolCall`, and `ToolResult`;
- `ModelConfiguration`;
- `ModelRequest`;
- `EgressDecision`;
- `ModelResponse`;
- `Event`;
- `ArtifactReference` and `Artifact`;
- `StopReason`;
- `RunResult`.

The first vertical slice may defer:

- workspace mutations;
- invalidation and refresh;
- patch artifacts;
- validation contracts in active use;
- command execution;
- publication.

The deferred contracts should still remain semantically stable enough that later features do not require redefining the first-slice objects.
