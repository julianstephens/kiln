# Kiln Events

## Status

Draft

## Purpose

This document defines Kiln's event model.

Events are the authoritative history of what happened during a run. They support:

- audit;
- inspection;
- replay;
- evaluation;
- debugging;
- recovery;
- usage analysis;
- security review.

This document defines:

- event semantics;
- event envelope;
- ordering;
- causation and correlation;
- event taxonomy;
- payload versus artifact rules;
- event production requirements;
- replay requirements;
- privacy and retention rules;
- initial vertical-slice requirements.

It does not define:

- concrete database tables;
- serialization encoding;
- generated language types;
- observability vendor integration;
- user-interface presentation;
- long-term archival infrastructure.

---

# 1. Event principles

## 1.1 Events record facts

An event records a fact that has occurred.

Events do not represent:

- intentions that were never persisted;
- speculative future state;
- mutable current state;
- arbitrary logs;
- unstructured diagnostic output.

Examples:

- a run was created;
- a repository query started;
- a capability was denied;
- a context item was admitted;
- a model response was received;
- a budget reservation was committed;
- validation completed.

## 1.2 Events are immutable

Once committed, an event cannot be edited or deleted individually as part of normal runtime behavior.

Corrections are represented by later events.

## 1.3 Events are append-oriented

Events are appended in run order.

The event store may compact physical storage, but logical event history remains append-only.

## 1.4 Events store first-class facts

Events contain enough structured facts to understand what happened.

Large content is stored as artifacts and referenced by identity.

## 1.5 Events are not state

The event stream answers:

> What happened?

The state store answers:

> What is true now?

Current state may be reconstructed from events, but Kiln may maintain materialized state for efficient access.

## 1.6 Events must support replay

The event history must preserve enough information to reconstruct:

- lifecycle transitions;
- model-visible context;
- repository operations;
- capability decisions;
- budget usage;
- workspace mutations;
- validation outcomes;
- terminal result.

Replay may still require referenced artifacts.

## 1.7 Events are security-sensitive

Event payloads may reveal:

- repository structure;
- paths;
- model usage;
- security policy;
- denied operations;
- task metadata.

The event store must apply the same installation or tenant scope as the run.

---

# 2. Event ownership

## 2.1 Runtime ownership

The Go runtime owns the authoritative event stream.

Workers and adapters return structured facts, but they do not append directly to the authoritative store.

## 2.2 Component responsibilities

Components produce event facts for the runtime.

Examples:

- repository engine returns query metadata;
- model gateway returns provider usage;
- capability broker returns authorization outcome;
- validator returns check results;
- workspace manager returns mutation facts.

The runtime validates and persists the event.

## 2.3 External systems

Hosted infrastructure may emit operational telemetry separately.

External telemetry does not replace Kiln's domain event stream.

---

# 3. Event envelope

Every event uses a common envelope.

## 3.1 Required fields

An event contains:

- event identity;
- event schema version;
- run identity;
- run sequence;
- event type;
- event timestamp;
- producer component;
- structured payload;
- causation identity, when applicable;
- correlation identity, when applicable.

Conceptually:

```text
Event
├── event_id
├── schema_version
├── run_id
├── sequence
├── event_type
├── occurred_at
├── producer
├── payload
├── causation_id?
├── correlation_id?
├── operation_id?
├── turn_id?
├── repository_session_id?
└── artifact_references?
```

## 3.2 Event identity

Event identity is globally unique within the installation or tenant scope.

It is stable and immutable.

## 3.3 Run sequence

Every event in a run has a monotonically increasing sequence number.

Sequence defines authoritative ordering within a run.

Wall-clock timestamps do not define ordering.

## 3.4 Event timestamp

`occurred_at` records when the event fact occurred according to the runtime.

Component-local timestamps may be included in payloads for diagnostics.

## 3.5 Producer

The producer identifies the logical component that supplied the event fact.

Examples:

- `run_coordinator`;
- `agent_loop`;
- `context_manager`;
- `budget_manager`;
- `capability_broker`;
- `model_gateway`;
- `repository_engine`;
- `workspace_manager`;
- `validator`;
- `publisher`.

Producer identity does not grant authority.

## 3.6 Payload

The payload contains event-type-specific first-class facts.

Payload schemas are versioned by event type.

## 3.7 Artifact references

Events may reference zero or more artifacts.

The event does not assume artifact bytes are embedded.

---

# 4. Ordering model

## 4.1 Per-run total order

Events are totally ordered within one run.

The runtime serializes event commits.

## 4.2 Cross-run ordering

Kiln does not require a total order across runs.

Cross-run analysis may use timestamps, installation sequence, or correlation identifiers.

## 4.3 Atomic transition events

A lifecycle state transition and its primary lifecycle event are committed atomically.

## 4.4 Operation ordering

Operation events should follow:

```text
planned
→ authorized or denied
→ reserved
→ started
→ completed or failed/cancelled/interrupted/exhausted
```

Not every operation requires every intermediate event, but actual history must remain internally consistent.

## 4.5 Out-of-order worker responses

Workers may complete concurrently or return responses out of order.

The runtime appends events in the order it accepts and commits the outcomes.

Causation and operation identities preserve logical relationships.

---

# 5. Causation and correlation

## 5.1 Causation

`causation_id` identifies the event or operation that directly caused this event.

Examples:

- a model response causes a tool proposal;
- a tool proposal causes an authorization decision;
- a workspace mutation causes invalidation;
- a completion proposal causes output production.

## 5.2 Correlation

`correlation_id` groups events belonging to one larger activity.

Examples:

- one model invocation;
- one repository query;
- one turn;
- one validation request;
- one refresh operation;
- one hosted workflow.

## 5.3 Operation identity

`operation_id` identifies a bounded runtime operation.

All attempts of one logical operation may share a parent correlation while having distinct attempt identities.

## 5.4 Turn identity

Events occurring within an agent turn should carry the turn identity.

## 5.5 Relationship invariants

- causation must refer to an earlier committed event or known operation;
- correlation may span components;
- operation identity must be unique within a run;
- retries use new attempt identities;
- terminal events preserve the causal chain to the triggering condition.

---

# 6. Event schema versioning

Every event includes an event schema version.

Compatibility rules:

- event type and schema version jointly define payload semantics;
- required fields cannot be removed within a compatible version;
- new optional fields may be added;
- changed semantics require a new schema version;
- consumers must reject event versions they cannot safely interpret;
- replay tooling must report unsupported event types rather than silently skipping required events.

Event taxonomy versioning is separate from runtime package versioning.

---

# 7. Payload versus artifact policy

## 7.1 Inline event facts

Store inline when the data is necessary to understand, query, or index the event.

Examples:

- status;
- state transition;
- operation identity;
- repository identity;
- content identities;
- model name;
- usage counts;
- budget domain;
- decision reason;
- changed-file paths, when bounded;
- error code;
- validation outcome;
- artifact identities and hashes.

## 7.2 Artifact content

Store as artifact blobs when content is:

- large;
- sensitive;
- binary;
- repeated;
- consumed or generated as a product;
- not needed for ordinary event filtering.

Examples:

- rendered model request;
- complete model response;
- source snapshot;
- repository candidate batch;
- patch;
- test logs;
- command stdout and stderr;
- context snapshot;
- validation report details;
- final result bundle.

## 7.3 Thresholds

Implementations may use configurable inline-size thresholds.

Threshold decisions must not change semantic meaning.

A consumer must be able to determine whether content is:

- inline;
- artifact-backed;
- truncated;
- omitted by policy.

## 7.4 Content hashes

Artifact references include content hashes.

Where useful, inline content may also include a hash for integrity and deduplication.

## 7.5 No silent truncation

If event payload data is truncated:

- truncation is explicit;
- original size is recorded where available;
- an artifact reference is provided when retained;
- omission reason is recorded when not retained.

---

# 8. Event categories

Kiln defines these top-level categories:

- run lifecycle;
- runtime session;
- turn lifecycle;
- repository;
- context;
- policy;
- model;
- budget;
- capability;
- tool;
- workspace;
- artifact;
- validation;
- recovery;
- error and diagnostic;
- publication.

Publication events may live in a separate workflow stream because publication is outside the run lifecycle.

---

# 9. Run lifecycle events

## 9.1 `run.created`

Records acceptance of a run specification.

Payload includes:

- run specification identity;
- task identity or hash;
- repository reference;
- requested model;
- requested policy;
- requested budgets;
- requested security profile;
- validation requirement.

Large task content may be artifact-backed.

## 9.2 `run.initialization_started`

Payload includes:

- initialization operation identity;
- selected runtime session;
- requested adapters.

## 9.3 `run.initialization_completed`

Payload includes:

- effective budgets;
- effective capability profile;
- selected adapter identities;
- deadline;
- initialization duration.

## 9.4 `run.execution_started`

Payload includes:

- repository session identity;
- base repository version;
- workspace version;
- initial turn identity.

## 9.5 `run.output_production_started`

Payload includes:

- completion proposal identity;
- output requirements;
- expected artifacts.

## 9.6 `run.output_production_completed`

Payload includes:

- final answer reference;
- patch reference, when applicable;
- changed-file manifest reference;
- usage summary;
- validation requirement.

## 9.7 `run.completed`

Payload includes:

- successful stop reason;
- final result reference;
- final usage summary;
- validation report reference, when applicable.

## 9.8 `run.failed`

Payload includes:

- failure stop reason;
- failure category;
- last successful lifecycle state;
- failure detail reference;
- partial result references;
- cleanup status.

## 9.9 `run.cancellation_requested`

Payload includes:

- requester;
- reason;
- requested timestamp;
- affected operation identities.

## 9.10 `run.cancellation_accepted`

Payload includes:

- accepted timestamp;
- cancellation mode;
- in-flight operations.

## 9.11 `run.cancelled`

Payload includes:

- cancellation stop reason;
- requester;
- interrupted operation identities;
- partial result references;
- final usage summary.

## 9.12 `run.exhausted`

Payload includes:

- exhaustion stop reason;
- budget domain;
- configured limit;
- committed usage;
- triggering operation;
- partial result references.

---

# 10. Runtime session events

The privately supervised Go child process has a runtime-session lifecycle distinct from a run.

## 10.1 `runtime.session_started`

Payload includes:

- runtime session identity;
- runtime version;
- protocol version;
- parent process identity metadata;
- database identity;
- startup timestamp.

## 10.2 `runtime.session_ready`

Payload includes:

- supported protocol capabilities;
- loaded database schema version;
- available adapters.

## 10.3 `runtime.session_stopping`

Payload includes:

- stop reason;
- active runs;
- shutdown deadline.

## 10.4 `runtime.session_stopped`

Payload includes:

- exit status;
- interrupted run identities;
- shutdown completeness.

## 10.5 `runtime.session_failed`

Payload includes:

- failure code;
- failure artifact reference;
- affected runs.

Runtime-session events may be stored in an installation-level stream and referenced by run events.

---

# 11. Turn events

## 11.1 `turn.started`

Payload includes:

- turn identity;
- turn number;
- task-state version;
- context-state version;
- workspace version;
- remaining budget snapshot.

## 11.2 `turn.completed`

Payload includes:

- turn identity;
- resulting task-state version;
- resulting context-state version;
- model invocation identities;
- tool and repository operation identities;
- turn usage;
- stop-controller outcome.

## 11.3 `turn.failed`

Payload includes:

- turn identity;
- failure code;
- causal operation;
- retryability.

---

# 12. Repository events

## 12.1 `repository.registration_started`

Payload includes:

- repository reference;
- workspace identity;
- registration operation.

## 12.2 `repository.registered`

Payload includes:

- repository identity;
- workspace identity;
- canonical source identity;
- whether existing registration was reused.

## 12.3 `repository.preparation_started`

Payload includes:

- repository identity;
- requested revision;
- expected digest;
- indexing configuration identity;
- requested refresh policy.

## 12.4 `repository.preparation_checkpointed`

Payload includes:

- preparation operation;
- completed stage;
- checkpoint identity;
- current index status.

## 12.5 `repository.version_pinned`

Payload includes:

- repository version identity;
- source revision;
- content digest.

## 12.6 `repository.preparation_completed`

Payload includes:

- repository version;
- workspace version;
- preparation mode;
- index status;
- preparation usage;
- diagnostics summary.

## 12.7 `repository.session_opened`

Payload includes:

- repository session identity;
- repository identity;
- repository version;
- workspace version;
- allowed operation set.

## 12.8 `repository.session_advanced`

Payload includes:

- repository session identity;
- prior workspace version;
- new workspace version;
- refresh operation identity.

## 12.9 `repository.session_closed`

Payload includes:

- session identity;
- close reason;
- outstanding-operation disposition.

## 12.10 `repository.query_started`

Payload includes:

- query operation;
- query type;
- bounded query summary or query artifact;
- session identity;
- requested limits;
- budget reservation.

## 12.11 `repository.query_completed`

Payload includes:

- query operation;
- result count;
- candidate identities;
- truncation status;
- repository usage;
- candidate-batch artifact reference, where applicable.

## 12.12 `repository.query_failed`

Payload includes:

- query operation;
- error code;
- retryability;
- diagnostics.

## 12.13 `repository.invalidated`

Payload includes:

- prior workspace version;
- new workspace version;
- mutation identities;
- stale content identities or bounded summary;
- invalidation reason.

## 12.14 `repository.refresh_started`

Payload includes:

- target workspace version;
- requested refresh mode;
- stale evidence summary;
- budget reservation.

## 12.15 `repository.refresh_completed`

Payload includes:

- refresh mode used;
- updated files;
- updated symbol count;
- updated relation count;
- remaining stale evidence;
- resulting index status;
- usage.

## 12.16 `repository.refresh_failed`

Payload includes:

- error code;
- retryability;
- partial progress;
- whether full rebuild is required.

## 12.17 `repository.worker_started`

Payload includes:

- worker session identity;
- protocol version;
- parser and index versions;
- supported operations.

## 12.18 `repository.worker_failed`

Payload includes:

- worker session identity;
- active operations;
- persisted-state safety;
- failure details reference.

---

# 13. Context events

## 13.1 `context.plan_requested`

Payload includes:

- policy identity;
- task-state version;
- context-state version;
- candidate identities;
- remaining budgets.

## 13.2 `context.plan_produced`

Payload includes:

- plan identity;
- policy identity;
- action summary;
- retrieval proposals;
- estimated cost;
- plan artifact reference, when large.

## 13.3 `context.plan_rejected`

Payload includes:

- plan identity;
- rejection reason;
- invalid actions;
- budget or version conflicts.

## 13.4 `context.plan_applied`

Payload includes:

- plan identity;
- resulting context-state version;
- admitted, evicted, compressed, and preserved item identities;
- resulting estimated token total.

## 13.5 `context.item_available`

Payload includes:

- context item identity;
- candidate identity;
- representation;
- repository and workspace versions;
- estimated tokens.

## 13.6 `context.item_admitted`

Payload includes:

- context item identity;
- representation;
- admission reason;
- policy identity;
- active-context position or class;
- estimated tokens.

## 13.7 `context.item_rejected`

Payload includes:

- candidate identity;
- rejection reason;
- policy identity.

## 13.8 `context.item_evicted`

Payload includes:

- context item identity;
- eviction reason;
- last-used turn;
- estimated tokens released.

## 13.9 `context.item_compressed`

Payload includes:

- prior item identity;
- replacement item identity;
- source and target representations;
- estimated token reduction;
- compression provenance.

## 13.10 `context.item_invalidated`

Payload includes:

- context item identity;
- repository or workspace version conflict;
- invalidation reason;
- whether item was active.

## 13.11 `context.rendered`

Payload includes:

- render identity;
- active context identities;
- message count;
- estimated input tokens;
- provenance-map artifact reference;
- rendered-request artifact reference.

---

# 14. Policy events

## 14.1 `policy.invocation_started`

Payload includes:

- policy identity;
- policy version;
- input artifact or input identity references;
- deadline.

## 14.2 `policy.invocation_completed`

Payload includes:

- policy identity;
- plan identity;
- duration;
- output summary.

## 14.3 `policy.invocation_failed`

Payload includes:

- error code;
- retryability;
- fallback policy, when used.

## 14.4 `policy.retrieval_proposed`

Payload includes:

- retrieval proposal identity;
- query kind;
- requested limits;
- justification or score summary.

Policy events do not imply that proposed actions were authorized or performed.

---

# 15. Model events

## 15.1 `model.request_rendered`

Payload includes:

- model invocation identity;
- render identity;
- model configuration identity;
- estimated input tokens;
- reserved output tokens;
- request artifact reference.

## 15.2 `model.egress_evaluated`

Payload includes:

- provider;
- endpoint identity;
- content identities;
- excluded or redacted content;
- decision;
- security-policy identity;
- byte and token estimates.

## 15.3 `model.invocation_started`

Payload includes:

- model invocation identity;
- provider;
- model;
- budget reservation;
- request artifact reference;
- attempt number.

## 15.4 `model.invocation_completed`

Payload includes:

- model invocation identity;
- finish reason;
- estimated input tokens;
- actual input tokens;
- actual output tokens;
- provider request identity, when safe;
- response artifact reference;
- duration.

## 15.5 `model.invocation_failed`

Payload includes:

- error code;
- provider error category;
- retryability;
- usage known before failure;
- attempt number.

## 15.6 `model.response_interpreted`

Payload includes:

- response identity;
- proposed tool calls;
- retrieval proposals;
- completion proposal;
- malformed proposal count;
- interpretation diagnostics.

Model response content remains artifact-backed when large.

---

# 16. Budget events

## 16.1 `budget.initialized`

Payload includes:

- configured budget domains;
- effective limits;
- source configuration identity.

## 16.2 `budget.reserved`

Payload includes:

- reservation identity;
- budget domain;
- amount;
- operation identity;
- remaining unreserved amount.

## 16.3 `budget.committed`

Payload includes:

- reservation identity;
- estimated amount;
- actual amount;
- released amount;
- operation identity;
- remaining amount.

## 16.4 `budget.released`

Payload includes:

- reservation identity;
- released amount;
- release reason.

## 16.5 `budget.denied`

Payload includes:

- requested amount;
- available amount;
- operation identity;
- denial reason.

## 16.6 `budget.exhausted`

Payload includes:

- budget domain;
- configured limit;
- committed usage;
- reserved usage;
- triggering operation.

## 16.7 `budget.reconciled`

Payload includes:

- candidate estimate;
- rendered estimate;
- provider actual usage;
- estimation error;
- reconciliation identity.

---

# 17. Capability events

## 17.1 `capability.granted`

Payload includes:

- capability grant identity;
- capability type;
- scope;
- target;
- source of authority;
- expiration.

## 17.2 `capability.narrowed`

Payload includes:

- original grant;
- narrowed grant;
- narrowing reason.

## 17.3 `capability.checked`

Payload includes:

- requested operation;
- required capability;
- grant identities considered;
- decision.

High-volume installations may omit successful low-risk checks from the first-class stream only if an equivalent aggregated audit event is retained. The initial implementation should record them.

## 17.4 `capability.denied`

Payload includes:

- requested operation;
- capability type;
- target;
- denial reason;
- model or tool proposal identity.

## 17.5 `capability.revoked`

Payload includes:

- grant identity;
- revocation reason;
- actor;
- effective timestamp.

---

# 18. Tool events

## 18.1 `tool.call_proposed`

Payload includes:

- tool call identity;
- tool identity;
- arguments artifact or bounded summary;
- model response identity;
- required capabilities.

## 18.2 `tool.call_validated`

Payload includes:

- tool call identity;
- schema version;
- validation outcome;
- normalized arguments reference.

## 18.3 `tool.execution_started`

Payload includes:

- execution operation;
- tool identity;
- budget reservation;
- sandbox or worker identity.

## 18.4 `tool.execution_completed`

Payload includes:

- execution operation;
- status;
- duration;
- usage;
- result artifact references;
- result candidate identities.

## 18.5 `tool.execution_failed`

Payload includes:

- error code;
- retryability;
- partial result references;
- effect certainty.

## 18.6 `tool.execution_cancelled`

Payload includes:

- cancellation reason;
- partial effect status;
- cleanup result.

---

# 19. Workspace events

## 19.1 `workspace.mutation_proposed`

Payload includes:

- mutation proposal identity;
- target paths;
- mutation kinds;
- source model or tool proposal.

## 19.2 `workspace.mutation_authorized`

Payload includes:

- mutation operation;
- capability grant;
- allowed paths;
- denied paths.

## 19.3 `workspace.mutation_applied`

Payload includes:

- prior workspace version;
- new workspace version;
- changed paths;
- prior and new content hashes;
- patch artifact reference.

## 19.4 `workspace.mutation_failed`

Payload includes:

- error code;
- effect certainty;
- rollback status.

## 19.5 `workspace.patch_created`

Payload includes:

- base repository version;
- final workspace version;
- changed-file count;
- patch artifact;
- patch hash.

---

# 20. Artifact events

Artifacts are stored as blobs in the installation database.

## 20.1 `artifact.created`

Payload includes:

- artifact identity;
- run identity;
- artifact kind;
- content type;
- content hash;
- uncompressed size;
- stored size;
- compression;
- retention class;
- access scope.

## 20.2 `artifact.reused`

Payload includes:

- artifact identity;
- matching content hash;
- new logical reference.

## 20.3 `artifact.accessed`

Payload includes:

- artifact identity;
- requester component;
- operation identity;
- access purpose.

Artifact access events may be aggregated for low-risk internal reads, but security-sensitive reads should remain explicit.

## 20.4 `artifact.deleted`

Payload includes:

- artifact identity;
- deletion reason;
- retention policy;
- actor.

Logical deletion or garbage collection does not alter prior events referencing the artifact. Those events indicate that the artifact is no longer retained.

## 20.5 `artifact.exported`

Payload includes:

- artifact identity;
- export destination class;
- actor;
- export policy;
- exported hash.

---

# 21. Validation events

## 21.1 `validation.request_created`

Payload includes:

- validation identity;
- run identity;
- base repository version;
- source snapshot artifact;
- patch artifact;
- validation profile;
- security profile;
- validation budget.

## 21.2 `validation.started`

Payload includes:

- validation identity;
- attempt identity;
- validator identity;
- execution environment identity.

## 21.3 `validation.workspace_materialized`

Payload includes:

- validation identity;
- source digest;
- patch applicability;
- temporary workspace identity, if safe.

## 21.4 `validation.check_started`

Payload includes:

- check identity;
- check type;
- command or policy identity;
- timeout.

## 21.5 `validation.check_completed`

Payload includes:

- check identity;
- status;
- duration;
- bounded summary;
- output artifact references.

## 21.6 `validation.report_received`

Payload includes:

- validation identity;
- report status;
- publication eligibility;
- approval requirement;
- report artifact reference.

## 21.7 `validation.completed`

Payload includes:

- validation identity;
- final status;
- passed check count;
- failed check count;
- report reference;
- total usage.

## 21.8 `validation.failed`

Payload includes:

- validation identity;
- failure type;
- failed checks;
- report reference.

## 21.9 `validation.error`

Payload includes:

- validation identity;
- infrastructure error;
- retryability;
- attempt number.

---

# 22. Recovery events

## 22.1 `run.recovery_claimed`

Payload includes:

- run identity;
- prior runtime session;
- new runtime session;
- persisted lifecycle state;
- recovery lease identity.

## 22.2 `run.recovery_started`

Payload includes:

- recoverable state;
- checkpoint identity;
- recovery strategy.

## 22.3 `repository.preparation_resumed`

Payload includes:

- prior checkpoint;
- first resumed stage;
- worker identity.

## 22.4 `validation.resumed`

Payload includes:

- validation request identity;
- prior attempt status;
- next attempt number.

## 22.5 `run.recovery_completed`

Payload includes:

- resumed lifecycle state;
- restored session identities;
- duration.

## 22.6 `run.recovery_failed`

Payload includes:

- failure code;
- checkpoint;
- resulting terminal reason.

---

# 23. Error and diagnostic events

## 23.1 `error.occurred`

Used for material errors that do not already have a more specific event type.

Payload includes:

- normalized error code;
- category;
- severity;
- component;
- operation identity;
- retryability;
- message safe for logs;
- detail artifact reference.

## 23.2 `diagnostic.recorded`

Used for non-terminal structured diagnostics.

Payload includes:

- diagnostic code;
- severity;
- component;
- path and source range, when applicable;
- related content identity;
- message;
- detail artifact reference.

## 23.3 Error privacy

Raw stack traces, provider responses, and command output should normally be artifact-backed.

Event payloads contain sanitized, bounded summaries.

---

# 24. Publication events

Publication is outside the run lifecycle.

Publication may use:

- a separate publication workflow stream;
- a correlation identity referencing the source run.

Suggested events:

- `publication.requested`;
- `publication.authorized`;
- `publication.branch_created`;
- `publication.commit_created`;
- `publication.pull_request_created`;
- `publication.failed`.

The source run remains terminal and unchanged.

---

# 25. Event persistence

## 25.1 Installation database

The default local deployment stores events in the installation database.

## 25.2 Transaction boundaries

At minimum, the following should commit atomically:

- lifecycle state transition and primary event;
- context-state mutation and corresponding context events;
- budget-ledger mutation and budget event;
- capability decision and capability event;
- workspace-version advancement and mutation/invalidation events;
- artifact creation metadata and artifact event.

## 25.3 Artifact blobs

Artifact metadata and blob bytes are stored in the database.

Large artifacts may be compressed.

## 25.4 Deduplication

Artifacts may be deduplicated by content hash.

Events retain logical artifact references even when physical bytes are shared.

## 25.5 Database growth

Implementations must support:

- retention policies;
- per-run deletion;
- artifact garbage collection;
- compaction;
- export;
- installation-wide size inspection.

Event metadata should normally be retained longer than large artifact blobs.

---

# 26. Replay requirements

## 26.1 Audit replay

Audit replay reconstructs what happened without re-executing external operations.

It requires:

- ordered events;
- referenced artifacts;
- schema interpretation;
- state transition rules.

## 26.2 Context replay

Context replay reconstructs what the model saw for each invocation.

It requires:

- context-plan events;
- context-state transitions;
- rendered-request artifacts;
- provenance-map artifacts;
- repository candidate identities and representations.

## 26.3 Policy replay

Policy replay evaluates a different context policy against recorded candidate sets.

It requires:

- policy inputs or reconstructable state;
- candidate-batch artifacts;
- budget snapshots;
- task and context state.

Policy replay does not claim to reproduce the original model trajectory unless model outputs are fixed.

## 26.4 Model replay

Model replay may use stored responses rather than invoking the provider.

It requires:

- rendered request artifact;
- response artifact;
- provider metadata;
- usage.

## 26.5 Full execution replay

Full execution replay may be impossible when:

- external state changed;
- artifacts were deleted;
- nondeterministic tools were used;
- historical repository versions are unavailable;
- unrecorded side effects occurred.

Kiln should distinguish:

- audit replay;
- deterministic simulation;
- partial replay;
- live re-execution.

## 26.6 Replay completeness

A run records a replay-completeness classification:

- `audit_complete`;
- `context_complete`;
- `policy_replayable`;
- `model_replayable`;
- `execution_replayable`;
- `partial`.

---

# 27. Evaluation requirements

Evaluation consumes events and artifacts without participating in the agent loop.

The event model should support metrics such as:

- task success;
- token use;
- model-call count;
- repository-query count;
- duplicate context;
- context churn;
- candidate admission rate;
- stale-evidence incidents;
- denied capability count;
- tool failure rate;
- validation success;
- wall time;
- cost;
- policy estimation error.

Evaluation outputs are separate artifacts or reports and do not rewrite source events.

---

# 28. Privacy and redaction

## 28.1 Sensitive fields

Potentially sensitive fields include:

- repository paths;
- source content;
- task prompts;
- model prompts and responses;
- command output;
- provider request identifiers;
- user or tenant identity;
- security-policy details.

## 28.2 Redaction

Redaction should occur before event commit when policy requires it.

The event records:

- that redaction occurred;
- the redaction policy;
- affected content categories;
- redacted artifact identity, when retained.

## 28.3 Secrets

Secrets must not be written to events or artifacts.

Secret scanning applies before persistence where practical.

Detected secrets produce security events and redacted output.

## 28.4 Access control

Event and artifact access is scoped by:

- installation;
- tenant, in hosted deployments;
- run;
- repository scope;
- requesting component;
- operation purpose.

---

# 29. Retention

## 29.1 Retention classes

Suggested classes:

- `ephemeral`;
- `run_default`;
- `audit`;
- `security`;
- `user_pinned`.

## 29.2 Metadata versus artifacts

Kiln may retain event metadata after deleting large artifact blobs.

The event then records artifact-retention status.

## 29.3 Deletion

Deletion must preserve consistency:

- artifact deletion does not delete event facts;
- run deletion removes or tombstones associated data according to policy;
- security and audit retention may override ordinary user retention;
- shared deduplicated blobs are deleted only when no retained reference remains.

---

# 30. Event query model

The event store should support queries by:

- run identity;
- sequence range;
- event type;
- category;
- operation identity;
- turn identity;
- correlation identity;
- repository identity;
- workspace version;
- terminal status;
- time range.

The event store should not expose arbitrary unscoped database access through public APIs.

---

# 31. Initial vertical-slice events

The first read-only milestone requires these events.

## Runtime and lifecycle

- `runtime.session_started`;
- `runtime.session_ready`;
- `run.created`;
- `run.initialization_started`;
- `run.initialization_completed`;
- `run.execution_started`;
- `run.output_production_started`;
- `run.output_production_completed`;
- one terminal run event.

## Repository

- `repository.preparation_started`;
- `repository.version_pinned`;
- `repository.preparation_completed`;
- `repository.worker_started`;
- `repository.session_opened`;
- `repository.query_started`;
- `repository.query_completed` or `repository.query_failed`;
- `repository.session_closed`.

## Context and policy

- `context.plan_requested`;
- `context.plan_produced`;
- `context.plan_applied`;
- `context.item_available`;
- `context.item_admitted`;
- `context.item_evicted`, when applicable;
- `context.rendered`.

## Model

- `model.request_rendered`;
- `model.egress_evaluated`;
- `model.invocation_started`;
- `model.invocation_completed` or `model.invocation_failed`;
- `model.response_interpreted`.

## Budget

- `budget.initialized`;
- `budget.reserved`;
- `budget.committed`;
- `budget.denied` or `budget.exhausted`, when applicable;
- `budget.reconciled`.

## Turn

- `turn.started`;
- `turn.completed` or `turn.failed`.

## Artifacts

- `artifact.created` for model request and response payloads;
- `artifact.created` for candidate batches when large;
- `artifact.created` for final result bundle.

---

# 32. Initial artifact kinds

The first milestone should support these artifact kinds:

- `run_specification`;
- `repository_candidate_batch`;
- `rendered_model_request`;
- `model_response`;
- `context_provenance_map`;
- `final_answer`;
- `final_result`;
- `error_detail`.

Later milestones add:

- `repository_snapshot`;
- `patch`;
- `command_output`;
- `test_report`;
- `validation_request`;
- `validation_report`;
- `publication_result`.

---

# 33. Event invariants

1. Events are immutable once committed.
2. Events are append-oriented.
3. Every event belongs to a scope.
4. Every run event has a monotonically increasing run sequence.
5. Run sequence, not timestamp, defines authoritative order.
6. Lifecycle transition and primary lifecycle event commit atomically.
7. Events record facts, not mutable current state.
8. Large content is artifact-backed.
9. Truncation and omission are explicit.
10. Artifact references include content hashes.
11. Causation refers to earlier facts or known operations.
12. Correlation groups related work across components.
13. Retries use distinct attempt identities.
14. Workers do not append directly to the authoritative event stream.
15. The runtime validates worker-provided event facts.
16. Model requests and responses are represented by events and artifacts.
17. Repository candidates are traceable to retrieval operations.
18. Context admissions are traceable to policy plans.
19. Capability decisions are traceable to requested operations.
20. Budget usage is traceable from reservation through reconciliation.
21. Workspace mutations are traceable to capability decisions and version advancement.
22. Validation reports are traceable to immutable validation requests.
23. Every terminal run has exactly one terminal event.
24. Terminal events include one stop reason.
25. Event history remains inspectable after cancellation, failure, or exhaustion.
26. Artifact deletion does not rewrite prior events.
27. Publication events do not reopen or modify terminal run lifecycle.
28. Secrets are not persisted in events or artifacts.
29. Event schema versions are explicit.
30. Unsupported required event schemas cause replay failure rather than silent omission.

---

# 34. Open event questions

The event model is sufficient for implementation planning. Remaining details include:

- exact event type naming convention;
- exact schema encoding;
- whether event IDs are globally sortable;
- artifact compression defaults;
- default inline payload threshold;
- exact retention defaults;
- whether successful capability checks may later be aggregated;
- installation-level event stream design;
- event subscription backpressure;
- hosted event export format;
- exact replay-completeness calculation;
- whether evaluation annotations belong in a separate event stream.

These questions do not change the core event semantics.
