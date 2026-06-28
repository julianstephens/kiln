# Kiln Repository Protocol

## Status

Draft

## Purpose

This document defines the protocol boundary between the Kiln runtime and the repository engine.

The repository protocol exists to provide structured, version-bound repository intelligence without allowing the repository engine to control:

- agent state;
- model context;
- budgets;
- capabilities;
- lifecycle transitions;
- publication;
- validation.

The runtime owns authority and orchestration.

The repository engine owns repository analysis and evidence production.

This document defines:

- protocol roles;
- session semantics;
- supported operations;
- request and response envelopes;
- repository and workspace version rules;
- candidate semantics;
- invalidation and refresh behavior;
- limits and error handling;
- cancellation and retries;
- event expectations;
- initial vertical-slice requirements.

It does not define:

- concrete transport encoding;
- generated language bindings;
- database schema;
- parser implementation;
- ranking algorithms;
- embedding providers;
- provider-specific tokenizers.

---

## 1. Protocol goals

The repository protocol must:

1. preserve a strict separation between retrieval and context admission;
2. bind all evidence to repository and workspace versions;
3. prevent accidental cross-repository access;
4. support one shared installation database with scoped sessions;
5. support repository preparation, search, source retrieval, graph traversal, and alternate representations;
6. support mandatory invalidation and controlled refresh;
7. return structured evidence rather than prompt-ready strings;
8. remain closed to unknown operations;
9. support cancellation, retries, and bounded payloads;
10. produce enough metadata for provenance, budgeting, audit, and replay.

---

## 2. Protocol roles

### 2.1 Runtime

The runtime is the protocol client.

It owns:

- run identity;
- repository capabilities;
- repository session lifecycle;
- budget reservations;
- request authorization;
- result validation;
- context-policy invocation;
- stale-evidence enforcement;
- lifecycle transitions;
- events.

The runtime may request retrieval, but it does not directly inspect the repository engine's database.

### 2.2 Repository engine

The repository engine is the protocol server.

It owns:

- repository registration;
- repository preparation;
- file discovery;
- parsing;
- symbol extraction;
- relation construction;
- current-index maintenance;
- search;
- graph traversal;
- source retrieval;
- representation generation;
- token-cost estimates;
- invalidation;
- incremental refresh;
- full rebuild.

The repository engine does not:

- decide what enters model context;
- invoke models;
- grant capabilities;
- execute arbitrary commands;
- mutate the runtime's run state;
- publish changes;
- expose unrestricted database queries.

### 2.3 Repository worker

The repository worker is the isolated process hosting the repository engine.

It communicates with the runtime through a private, typed, versioned protocol.

The worker must not listen on a public interface.

---

## 3. Trust model

The repository engine is first-party but semi-trusted.

The runtime must validate all repository-engine responses.

Repository content is untrusted.

The protocol must assume repository files may contain:

- malformed syntax;
- extremely large files;
- generated content;
- prompt injection;
- invalid encodings;
- symlinks;
- cyclic imports;
- adversarial identifiers;
- parser-triggering edge cases.

Repository output is evidence, not instruction.

---

## 4. Transport requirements

The initial local transport should be one of:

- inherited stdin/stdout;
- private socket pair;
- Unix domain socket;
- Windows named pipe.

The transport must provide:

- private process-to-process communication;
- message framing;
- request-response correlation;
- cancellation;
- bounded message sizes;
- protocol-version negotiation;
- worker health detection;
- clean shutdown.

The worker must not open a public TCP port in embedded mode.

The semantic protocol should remain transport-independent.

---

## 5. Protocol envelope

Every request and response uses a common envelope.

### 5.1 Request envelope

A request contains:

- protocol version;
- request identity;
- run identity;
- repository-session identity, when required;
- operation name;
- operation payload;
- deadline;
- trace or correlation identity;
- capability reference;
- budget reservation reference, where applicable.

Conceptually:

```text
RepositoryRequest
├── protocol_version
├── request_id
├── run_id
├── session_id?
├── operation
├── payload
├── deadline
├── correlation_id?
├── capability_grant_id?
└── budget_reservation_id?
```

### 5.2 Response envelope

A response contains:

- protocol version;
- request identity;
- operation name;
- status;
- result payload or structured error;
- repository identity;
- repository version;
- workspace version;
- usage metadata;
- diagnostics;
- artifact references where applicable.

Conceptually:

```text
RepositoryResponse
├── protocol_version
├── request_id
├── operation
├── status
├── repository_id?
├── repository_version_id?
├── workspace_version_id?
├── result?
├── error?
├── usage?
├── diagnostics?
└── artifact_references?
```

### 5.3 Status values

Protocol-level response statuses are:

- `ok`;
- `not_found`;
- `invalid_request`;
- `denied`;
- `stale_session`;
- `conflict`;
- `cancelled`;
- `exhausted`;
- `retryable_error`;
- `fatal_error`.

Domain-specific outcome fields may provide additional detail.

---

## 6. Protocol versioning

The protocol version must be explicit in every request and response.

A worker must reject unsupported major versions.

Compatibility rules:

- major-version mismatch is fatal;
- minor versions may add optional fields;
- unknown required fields are rejected;
- unknown operations are rejected;
- unknown enum values are rejected unless explicitly marked extensible;
- clients must not infer support from worker implementation language or package version.

The initial protocol should prefer a closed operation set.

---

## 7. Repository identity model

The protocol distinguishes several related identities.

### 7.1 Workspace identity

Represents a registered local or hosted working environment.

A workspace may contain one or more logical repositories.

### 7.2 Repository identity

Represents one logical repository across revisions and workspace states.

Examples:

- a local Git repository;
- a hosted repository snapshot;
- an extracted source bundle.

### 7.3 Repository version identity

Represents one immutable base repository state.

It is typically bound to:

- a Git commit;
- a content digest;
- a snapshot identity;
- an import timestamp.

### 7.4 Workspace version identity

Represents one ordered mutable state derived from a repository version.

Every approved workspace mutation advances the workspace version.

### 7.5 Repository session identity

Represents one scoped protocol session bound to:

- one run;
- one repository;
- one repository version;
- one workspace version;
- one set of allowed operations.

A session prevents callers from issuing arbitrary cross-repository queries.

---

## 8. Session model

Repository operations occur through scoped sessions.

### 8.1 Session creation

The runtime opens a session after repository preparation.

Conceptually:

```text
repository.open
    input:
        run identity
        repository identity
        repository version
        workspace version
        allowed operation set
    output:
        repository session identity
        session capabilities
        current index status
```

### 8.2 Session scope

A repository session binds all later requests to:

- one run;
- one repository;
- one base repository version;
- one current workspace version;
- one security scope;
- one protocol version.

The caller does not repeat arbitrary repository identifiers on each operation.

### 8.3 Session advancement

When the workspace version advances, the existing session becomes stale until refreshed or advanced.

The runtime may request:

- session refresh;
- session advance to a new workspace version;
- session close and reopen.

The protocol must never silently change a session's version binding.

### 8.4 Session closure

Closing a session:

- releases transient worker resources;
- does not delete indexed repository state;
- does not delete run events;
- does not remove persisted repository versions.

### 8.5 Session expiration

Sessions may expire when:

- the owning run terminates;
- the worker restarts;
- the session deadline passes;
- the runtime explicitly closes it.

A restarted worker may require the runtime to reopen a logically equivalent session.

---

## 9. Repository preparation operations

### 9.1 `repository.register`

Registers or resolves a logical repository.

#### Consumes

- workspace identity;
- repository root or snapshot reference;
- canonical source identity, if known;
- repository name;
- source kind;
- configuration identity.

#### Produces

- repository identity;
- resolved metadata;
- whether the repository already existed;
- current known repository versions.

#### Rules

- registration does not imply indexing;
- root paths must be normalized and scoped;
- repository identity must not be derived solely from a mutable path;
- hosted snapshots may use content identity instead of a local path.

---

### 9.2 `repository.prepare`

Prepares one repository version and current workspace version for retrieval.

#### Consumes

- repository identity;
- requested revision or snapshot;
- expected content digest, when available;
- indexing configuration;
- language configuration;
- ignore rules;
- refresh policy;
- operation budget.

#### Produces

- repository version identity;
- workspace version identity;
- source revision;
- content digest;
- index state;
- preparation mode;
- diagnostics;
- readiness status.

#### Preparation modes

The result identifies one of:

- `reused_current_index`;
- `incremental_refresh`;
- `full_rebuild`;
- `new_index`;
- `failed`.

#### Rules

- preparation must be idempotent for the same immutable inputs;
- partial index updates must commit atomically;
- incomplete preparation must not appear current;
- repository preparation may be resumed from checkpoints;
- current-index compatibility must include schema and configuration compatibility.

---

### 9.3 `repository.status`

Returns preparation and index status.

#### Consumes

- repository identity or preparation operation identity.

#### Produces

- repository version;
- workspace version;
- current-index state;
- stale file count;
- refresh state;
- preparation checkpoints;
- diagnostics.

---

## 10. Retrieval operations

The initial protocol supports these retrieval families:

- search;
- source;
- file;
- graph;
- representation;
- outline or summary.

Every retrieval response returns structured candidates.

### 10.1 `repository.search`

Performs repository search.

#### Consumes

- repository session identity;
- search query;
- search modes;
- result limit;
- optional path scope;
- optional semantic-kind filters;
- optional representation preference;
- optional minimum score;
- result-size limit.

#### Search modes

Possible modes include:

- lexical;
- full-text;
- symbol-name;
- qualified-name;
- semantic;
- hybrid.

The initial vertical slice may support only lexical or full-text search.

#### Produces

- ordered repository candidates;
- search diagnostics;
- result count;
- truncation status;
- usage metadata.

#### Rules

- results are scoped to the session;
- results must include repository and workspace versions;
- scores must be labeled by score type;
- ordering must be deterministic for equivalent inputs where possible;
- truncated results must be explicitly marked.

---

### 10.2 `repository.get_source`

Retrieves source for a file, symbol, or source range.

#### Consumes

- repository session identity;
- target content identity or path;
- optional qualified name;
- optional source range;
- representation preference;
- maximum result size.

#### Produces

- one or more repository candidates;
- exact source location;
- source digest;
- line and byte ranges;
- token estimate;
- truncation status.

#### Rules

- paths must remain within the scoped repository;
- symlink or junction escape is rejected;
- source identity must be stable within the repository version;
- line-ending normalization must be declared;
- truncated source must not masquerade as complete source.

---

### 10.3 `repository.get_file`

Retrieves file-level metadata and representations.

#### Consumes

- repository session identity;
- file identity or path;
- representation preference;
- include metadata flags.

#### Produces

Possible candidate representations:

- file metadata;
- file outline;
- file summary;
- filtered source;
- full source.

---

### 10.4 `repository.expand_graph`

Traverses repository relationships.

#### Consumes

- repository session identity;
- starting content identities;
- relation types;
- direction;
- maximum depth;
- maximum nodes;
- maximum edges;
- confidence threshold;
- representation preference.

#### Relation types

Possible relation types include:

- calls;
- called_by;
- imports;
- imported_by;
- contains;
- contained_by;
- references;
- referenced_by;
- implements;
- overrides;
- inherits;
- depends_on.

The initial vertical slice may support one relation family.

#### Produces

- graph-path candidates;
- node candidates;
- edge metadata;
- unresolved-edge diagnostics;
- truncation status;
- traversal usage.

#### Rules

- graph traversal must be bounded;
- cycles must be detected;
- every relation includes confidence or derivation type;
- unresolved relations remain explicit;
- traversal does not imply source admission.

---

### 10.5 `repository.get_representation`

Requests a specific representation for known content.

#### Consumes

- repository session identity;
- content identity;
- requested representation;
- maximum token estimate;
- optional compression profile.

#### Produces

- repository candidate in requested or fallback representation;
- available alternatives;
- representation provenance;
- estimate metadata.

#### Representation kinds

Possible kinds include:

- repository summary;
- package summary;
- file summary;
- file outline;
- symbol signature;
- symbol summary;
- filtered source;
- full source;
- graph path;
- search snippet.

#### Fallback behavior

When the requested representation is unavailable, the engine may:

- return `not_found`;
- return a declared fallback;
- return available alternatives.

Fallback must never be silent.

---

### 10.6 `repository.list_representations`

Lists available representations for content.

#### Consumes

- repository session identity;
- content identity.

#### Produces

- available representation kinds;
- token estimates;
- generation status;
- artifact references where applicable.

---

## 11. Repository candidate contract

A repository candidate is the primary evidence unit returned by the repository engine.

### 11.1 Required identity fields

A candidate includes:

- content identity;
- repository identity;
- repository version identity;
- workspace version identity;
- semantic kind;
- representation kind.

### 11.2 Source fields

When source-backed, a candidate includes:

- normalized repository-relative path;
- source digest;
- line range;
- byte range, where available;
- qualified name, where available;
- language, where known.

### 11.3 Content fields

A candidate provides one of:

- inline bounded content;
- artifact reference;
- structured representation payload.

The response must declare which form is used.

### 11.4 Cost fields

A candidate includes advisory estimates:

- estimated tokens;
- estimated bytes;
- estimation method;
- tokenizer family, if known;
- estimate confidence, if available.

Repository estimates are advisory.

The model gateway performs final provider-specific counting.

### 11.5 Relevance fields

A candidate may include:

- lexical score;
- semantic score;
- hybrid score;
- graph distance;
- match terms;
- rank;
- score explanation.

Scores must be labeled and must not be treated as universally comparable across methods.

### 11.6 Provenance fields

A candidate includes:

- source operation identity;
- query identity;
- extraction or generation method;
- parser or summarizer version;
- source content identities;
- creation timestamp;
- whether generated or directly extracted.

### 11.7 Validity fields

A candidate includes:

- current or stale status;
- version binding;
- invalidation reason, when stale;
- synchronization status;
- completeness or truncation status.

### 11.8 Alternative representations

A candidate may advertise alternatives:

```text
AlternativeRepresentation
├── representation_kind
├── estimated_tokens
├── availability
├── generation_required
└── quality metadata
```

### 11.9 Candidate invariants

1. A candidate is bound to one repository version and workspace version.
2. A candidate cannot claim current status if invalidated.
3. Truncated content is explicitly marked.
4. Generated summaries identify their sources.
5. Token estimates declare their estimation method.
6. Candidate content is evidence, not instruction.
7. The engine does not mark candidates as admitted or active context.
8. Stable identities remain stable within the same repository version.
9. Candidate paths are repository-relative.
10. Cross-session candidates must still match the receiving session's version scope before use.

---

## 12. Current index and version journal

Kiln uses:

- one mutable current index;
- a version journal describing repository and workspace changes.

### 12.1 Mutable current index

The current index contains the active materialized state for:

- files;
- symbols;
- relations;
- representations;
- search structures;
- embeddings, when enabled.

### 12.2 Version journal

The journal records:

- repository versions;
- workspace versions;
- file mutations;
- invalidations;
- refresh operations;
- full rebuilds;
- configuration changes;
- index schema changes;
- content digests.

### 12.3 Historical queryability

The initial protocol does not require arbitrary queries against all historical versions.

Historical versions may be:

- metadata-only;
- reconstructable from snapshots and journals;
- periodically snapshotted;
- unavailable for live retrieval.

The current index is optimized for the active version.

### 12.4 Version transition rule

The engine must not expose a partially updated current index as a new workspace version.

A version transition becomes current only after:

- all required file updates commit;
- relation updates commit;
- index metadata updates commit;
- journal entry commits.

---

## 13. Invalidation operations

### 13.1 `repository.invalidate`

Marks evidence affected by workspace mutations as stale.

#### Consumes

- repository session identity;
- prior workspace version;
- new workspace version;
- mutation set;
- changed paths;
- optional content digests;
- mutation operation identity.

#### Produces

- invalidation summary;
- stale file identities;
- stale symbol identities;
- stale relation classes;
- stale representation identities;
- refresh recommendation;
- new session status.

#### Rules

- invalidation is synchronous with workspace-version advancement;
- affected evidence becomes stale before the mutation is considered complete;
- invalidation may be conservative;
- uncertain dependencies must be marked stale rather than assumed current;
- invalidation does not itself refresh the index.

---

### 13.2 Mutation set

A mutation set may contain:

- file created;
- file modified;
- file deleted;
- file renamed;
- configuration changed;
- ignore rules changed;
- language configuration changed.

Each mutation includes:

- prior path, where applicable;
- new path, where applicable;
- prior digest, where available;
- new digest, where available;
- mutation type;
- source operation identity.

---

## 14. Refresh operations

### 14.1 `repository.refresh`

Synchronizes stale repository intelligence.

#### Consumes

- repository session identity;
- target workspace version;
- refresh mode;
- optional path subset;
- operation budget;
- deadline.

#### Refresh modes

- `eager_incremental`;
- `lazy_incremental`;
- `batch_incremental`;
- `full_rebuild`;
- `auto`.

#### Produces

- refreshed workspace version;
- refresh mode actually used;
- updated files;
- updated symbols;
- updated relations;
- remaining stale evidence;
- new index status;
- diagnostics;
- usage metadata.

#### Rules

- `auto` may select incremental refresh or full rebuild;
- correctness overrides caller preference;
- full rebuild may be selected when incremental consistency is uncertain;
- refreshed evidence must not become current until commit succeeds;
- refresh must record journal entries;
- final reasoning and validation require required evidence to be current.

---

### 14.2 `repository.refresh_status`

Returns refresh progress and stale-state information.

#### Produces

- active refresh operation;
- completed stages;
- stale file count;
- stale relation count;
- current workspace version;
- target workspace version;
- readiness.

---

### 14.3 `repository.advance_session`

Advances a session after successful invalidation and refresh.

#### Consumes

- repository session identity;
- expected prior workspace version;
- target workspace version.

#### Produces

- updated session binding;
- current index status;
- available operations.

#### Rules

- advancement is explicit;
- stale prior sessions remain invalid;
- session advancement fails on version conflict.

---

## 15. Preparation and refresh checkpoints

Repository preparation and refresh are recoverable operations.

The engine should checkpoint idempotent stages such as:

- source resolution;
- file enumeration;
- hash calculation;
- parse completion;
- symbol extraction;
- relation construction;
- representation generation;
- FTS update;
- vector index update;
- current-index commit;
- journal commit.

A restarted worker may resume from committed checkpoints.

Incomplete transactions must be rolled back or repeated.

---

## 16. Request limits

Every request must be bounded.

Possible limits include:

- maximum query length;
- maximum path-filter count;
- maximum result count;
- maximum inline bytes;
- maximum graph depth;
- maximum graph nodes;
- maximum graph edges;
- maximum source range;
- maximum operation time;
- maximum generated representation cost.

The runtime may impose stricter limits than the repository engine.

The engine must return explicit truncation or exhaustion metadata rather than silently dropping data.

---

## 17. Budget semantics

Repository operations may consume:

- repository-query count;
- repository-processing time;
- CPU time;
- generated representation budget;
- embedding budget;
- result-byte budget.

### 17.1 Reservation

The runtime reserves the applicable budget before starting a repository operation.

The request may carry the reservation identity.

### 17.2 Usage response

The engine reports operation usage such as:

- elapsed time;
- files scanned;
- candidates returned;
- bytes returned;
- graph nodes visited;
- representations generated;
- estimated tokens returned.

### 17.3 Reconciliation

The runtime commits actual usage and releases unused reservation.

The repository engine does not mutate the runtime budget ledger directly.

---

## 18. Cancellation

The runtime may cancel:

- preparation;
- search;
- graph traversal;
- representation generation;
- refresh;
- full rebuild.

### 18.1 `repository.cancel`

#### Consumes

- request or operation identity;
- cancellation reason.

#### Produces

- cancellation accepted or too-late status;
- final operation disposition.

### 18.2 Cancellation rules

- cancellation is best effort until acknowledged;
- completed atomic index commits remain valid;
- partial uncommitted changes are rolled back;
- cancellation does not delete reusable committed index work;
- cancelled operations return structured status;
- cancellation is recorded in events.

---

## 19. Retry semantics

The runtime may retry idempotent repository operations.

Generally retryable:

- status requests;
- bounded search;
- source retrieval;
- graph traversal;
- representation listing;
- session open;
- preparation stage after rollback;
- refresh stage after rollback.

Retry requires care when:

- generation uses nondeterministic summarization;
- external embedding services are involved;
- operation completion is uncertain;
- the worker died during commit.

Each retry creates a new attempt identity linked to the original operation.

The engine should provide idempotency keys for preparation and refresh operations.

---

## 20. Error contract

Errors are structured.

### 20.1 Error fields

A repository error includes:

- error code;
- category;
- message safe for logs;
- retryability;
- operation identity;
- repository session identity;
- repository and workspace versions;
- diagnostics;
- artifact references;
- causal error identity, where applicable.

### 20.2 Error categories

Suggested categories:

- protocol;
- authorization;
- session;
- version;
- repository;
- indexing;
- parsing;
- search;
- graph;
- representation;
- resource;
- persistence;
- cancellation;
- internal.

### 20.3 Important error codes

Examples:

- `unsupported_protocol_version`;
- `unknown_operation`;
- `invalid_request`;
- `session_not_found`;
- `session_expired`;
- `session_scope_mismatch`;
- `workspace_version_conflict`;
- `repository_version_conflict`;
- `stale_session`;
- `repository_not_found`;
- `path_outside_repository`;
- `content_not_found`;
- `representation_unavailable`;
- `index_not_ready`;
- `refresh_required`;
- `result_limit_exceeded`;
- `operation_cancelled`;
- `operation_exhausted`;
- `worker_unavailable`;
- `index_corrupt`;
- `internal_error`.

The runtime maps repository errors into operation and run-level outcomes.

The repository engine does not choose the run terminal state.

---

## 21. Diagnostics

Diagnostics are structured and distinct from errors.

Possible diagnostics include:

- parse failure;
- unsupported language;
- unresolved reference;
- duplicate symbol;
- truncated source;
- graph confidence warning;
- summary-generation warning;
- stale representation;
- ignored file;
- oversized file skipped.

A successful response may contain diagnostics.

Diagnostics include:

- diagnostic code;
- severity;
- path and range, where applicable;
- content identity;
- message;
- related artifact reference.

---

## 22. Event expectations

The repository engine does not own the authoritative event store, but it returns enough metadata for the runtime to emit events.

Expected runtime events include:

- `repository.registration_started`;
- `repository.registered`;
- `repository.preparation_started`;
- `repository.preparation_checkpointed`;
- `repository.preparation_completed`;
- `repository.session_opened`;
- `repository.session_closed`;
- `repository.query_started`;
- `repository.query_completed`;
- `repository.query_failed`;
- `repository.candidates_returned`;
- `repository.invalidation_started`;
- `repository.invalidated`;
- `repository.refresh_started`;
- `repository.refresh_completed`;
- `repository.refresh_failed`;
- `repository.session_advanced`;
- `repository.worker_started`;
- `repository.worker_stopped`;
- `repository.worker_failed`.

Large result payloads are stored as artifact blobs and referenced by events.

---

## 23. Worker lifecycle

### 23.1 Startup

On startup, the worker:

1. negotiates protocol version;
2. verifies database compatibility;
3. reports capabilities;
4. reports supported operations;
5. reports parser and index versions;
6. becomes ready.

### 23.2 Health

The runtime may request worker health.

Health includes:

- process status;
- database access;
- protocol status;
- active operation count;
- index migration status;
- degraded capability list.

### 23.3 Shutdown

Graceful shutdown:

- rejects new operations;
- cancels or completes active operations according to policy;
- commits or rolls back transactions;
- closes database resources;
- acknowledges shutdown.

### 23.4 Unexpected exit

On worker exit:

- transient sessions are lost;
- persisted current index and journal remain;
- active requests become interrupted;
- recoverable preparation or refresh may resume;
- the runtime decides whether the run can continue.

---

## 24. Security requirements

The repository worker must:

- receive only repository scopes granted by the runtime;
- reject paths outside the registered repository;
- reject symlink and junction escape;
- avoid inheriting the full host environment;
- avoid arbitrary network access by default;
- avoid command execution;
- expose no generic SQL endpoint;
- expose no arbitrary file-read endpoint;
- expose no dynamic operation registration;
- validate all request sizes;
- validate all content identities and paths;
- store no publication credentials.

The runtime must:

- validate every response;
- enforce session-to-run ownership;
- enforce capability grants;
- reject version mismatches;
- enforce budget and deadline limits;
- prevent cross-run session reuse;
- treat all returned content as untrusted evidence.

---

## 25. Initial vertical-slice protocol

The first vertical slice requires only:

- `repository.register`;
- `repository.prepare`;
- `repository.status`;
- `repository.open`;
- `repository.search`;
- `repository.get_source`;
- `repository.expand_graph`;
- `repository.get_representation`;
- `repository.close`;
- worker health and shutdown.

### 25.1 Initial constraints

- one local repository per run;
- read-only workspace;
- no workspace mutation;
- no invalidation or refresh during `running`;
- one repository session;
- one supported graph relation;
- bounded inline content;
- fixed repository-token estimates;
- no remote embeddings requirement;
- no arbitrary historical-version queries.

### 25.2 Initial success criteria

The protocol is sufficient when the runtime can:

1. register or resolve a local repository;
2. prepare and pin a repository version;
3. open a scoped session;
4. search for relevant symbols or text;
5. retrieve exact source;
6. expand one graph relation;
7. request an alternate representation;
8. validate that every candidate matches the session versions;
9. close the session;
10. persist enough metadata for replay and audit.

---

## 26. Repository protocol invariants

1. Every repository operation is associated with one run.
2. Every retrieval operation occurs through a scoped repository session.
3. A session is bound to one repository version and workspace version.
4. Session scope cannot change silently.
5. The engine exposes no generic query language or SQL endpoint.
6. Unknown operations are rejected.
7. Every candidate is version-bound.
8. Every candidate declares completeness or truncation.
9. Every candidate declares its representation kind.
10. Every candidate declares advisory cost estimates.
11. Repository estimates are not authoritative model-token counts.
12. Retrieval does not imply context admission.
13. Repository output never mutates agent state directly.
14. Repository output is treated as untrusted evidence.
15. Workspace mutation synchronously invalidates affected evidence.
16. Stale evidence cannot be returned as current.
17. Refresh commits atomically.
18. Partial refresh results do not become current.
19. The current index and version journal remain consistent.
20. Preparation and refresh are idempotent or checkpointed.
21. Cross-repository access is prevented by session scope.
22. Cross-run session reuse is rejected.
23. Paths are normalized and repository-relative.
24. Path escape is rejected.
25. Every request and response is bounded.
26. Cancellation and retries are explicit.
27. The engine reports usage but does not own the budget ledger.
28. The runtime owns lifecycle transitions.
29. Large payloads may be returned by artifact reference.
30. Worker restart does not invalidate committed index state, but it invalidates transient sessions.

---

## 27. Open protocol questions

The protocol boundary is defined well enough for implementation planning. The following details remain for later design:

- exact message encoding;
- exact framing for stdio or private sockets;
- candidate identity format;
- repository-session lease duration;
- exact search scoring schema;
- exact graph relation taxonomy;
- summary-generation ownership;
- whether generated representations are persisted eagerly or lazily;
- artifact blob transfer versus database-reference access;
- parser capability negotiation;
- index schema migration protocol;
- maximum default message sizes;
- detailed refresh checkpoint granularity;
- historical-version snapshot strategy.

These questions do not change the core protocol semantics.
