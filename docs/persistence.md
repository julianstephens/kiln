# Kiln Persistence

## Status

Draft

## Purpose

This document defines Kiln's persistence model.

Persistence supports:

- repository indexing;
- run state;
- event history;
- context state;
- budget accounting;
- capability grants;
- artifact storage;
- validation;
- recovery;
- replay;
- evaluation.

The default local deployment uses one embedded Turso-compatible database per user installation.

Kiln stores:

- a mutable current repository index;
- a version journal;
- materialized run state;
- immutable events;
- artifact blobs;
- validation records.

This document defines:

- database topology;
- logical domains;
- identity and scope;
- repository index materialization;
- version journaling;
- run-state persistence;
- event and artifact persistence;
- transaction boundaries;
- concurrency;
- recovery;
- retention and garbage collection;
- migrations;
- security;
- first-milestone requirements.

It does not define:

- exact SQL DDL;
- concrete column names;
- ORM choices;
- query-builder APIs;
- storage-engine tuning values;
- hosted object-storage layouts.

---

## 1. Persistence principles

### 1.1 One installation database

The default local topology is one database per Kiln installation.

Conceptually:

```text
~/.kiln/
└── kiln.db
```

This database may contain:

- multiple workspaces;
- multiple repositories;
- multiple runs;
- shared repository indexes;
- event history;
- artifact blobs;
- validation history.

Projects may contain lightweight configuration, but canonical persistent state belongs to the installation database.

### 1.2 Logical isolation is explicit

Every persisted object belongs to a logical scope.

Relevant scopes include:

- installation;
- tenant, in hosted deployments;
- workspace;
- repository;
- repository version;
- workspace version;
- run;
- validation;
- artifact.

Queries must be issued through scoped APIs.

Callers must not rely on remembering to append raw `WHERE` clauses correctly.

### 1.3 The current index is mutable

Kiln maintains one materialized current index for each active repository state.

The current index is optimized for retrieval.

It may be updated incrementally after workspace mutations.

### 1.4 History is journaled

Kiln records repository and workspace changes in a version journal.

The journal captures:

- base revisions;
- workspace-version transitions;
- file mutations;
- invalidations;
- refresh operations;
- rebuilds;
- configuration changes;
- index-schema changes.

The journal preserves history without requiring full index duplication for every version.

### 1.5 Events are immutable

Events are append-oriented facts.

They are never updated to represent current state.

### 1.6 State is materialized

Kiln stores current run state separately from event history for efficient access and recovery.

### 1.7 Artifacts are blobs

Large payloads and products are stored in the database as blobs.

Examples:

- prompts;
- model responses;
- candidate batches;
- patches;
- logs;
- validation reports.

### 1.8 Transactions preserve invariants

State changes that must remain consistent are committed atomically.

### 1.9 Recovery depends on durable checkpoints

Recoverable lifecycle states persist enough checkpoints to resume safely.

The initial recoverable states are:

- `preparing_repository`;
- `validating`.

### 1.10 Hosted topology may differ physically

The logical persistence model remains consistent across local and hosted deployments.

Hosted deployments may use:

- one database per tenant;
- one database per runner;
- one database per execution domain;
- external object storage for artifact bytes.

The default local topology remains one database per installation.

---

## 2. Installation layout

The local installation may contain:

```text
~/.kiln/
├── kiln.db
├── runtime/
├── locks/
└── exports/
```

### 2.1 `kiln.db`

Contains canonical structured state and artifact blobs.

### 2.2 `runtime/`

Contains transient runtime files such as:

- private socket endpoints;
- process ownership markers;
- temporary runtime metadata.

Transient runtime files are not the source of truth.

### 2.3 `locks/`

Contains optional process or migration lock files when database-native locking is insufficient.

### 2.4 `exports/`

Contains user-requested exports.

Exports are not canonical state unless explicitly re-imported.

---

## 3. Logical persistence domains

The installation database is divided into logical domains.

```text
Installation database
│
├── installation domain
├── workspace domain
├── repository domain
├── repository intelligence domain
├── runtime domain
├── event domain
├── artifact domain
├── validation domain
└── maintenance domain
```

These domains may share one physical database while retaining separate ownership rules.

---

## 4. Installation domain

The installation domain records database-wide metadata.

### 4.1 Installation identity

Represents one Kiln installation or hosted persistence domain.

Contains:

- installation identity;
- creation timestamp;
- database format version;
- schema version;
- runtime compatibility metadata;
- encryption metadata;
- maintenance state.

### 4.2 Runtime sessions

Tracks privately supervised Go runtime processes.

Contains:

- runtime-session identity;
- process ownership metadata;
- start and stop times;
- protocol version;
- runtime version;
- heartbeat or lease state;
- shutdown disposition.

### 4.3 Migration state

Contains:

- current schema version;
- migration history;
- migration status;
- failed migration details;
- compatibility bounds.

---

## 5. Workspace domain

A workspace represents a registered local or hosted working environment.

### 5.1 Workspace record

Contains:

- workspace identity;
- installation or tenant scope;
- root location or snapshot namespace;
- display name;
- registration time;
- last-seen time;
- active/inactive state;
- configuration identity.

### 5.2 Workspace identity rules

Workspace identity must not rely solely on a mutable filesystem path.

A workspace may be identified through:

- installation-generated stable identity;
- canonical root plus filesystem identity;
- hosted snapshot namespace;
- explicit caller-provided identity.

### 5.3 Workspace configuration

Workspace-specific configuration may include:

- ignore rules;
- language settings;
- indexing settings;
- security profile defaults;
- model defaults;
- validation defaults.

Configuration changes are versioned or journaled when they affect index semantics.

---

## 6. Repository domain

A repository represents one logical codebase across revisions and workspace states.

### 6.1 Repository record

Contains:

- repository identity;
- workspace identity;
- canonical source identity;
- repository name;
- source kind;
- default branch or revision metadata;
- registration time;
- current repository-version identity;
- current workspace-version identity;
- active/inactive state.

### 6.2 Canonical source identity

Examples:

- normalized Git remote identity;
- local repository identity;
- hosted repository identifier;
- snapshot namespace.

Credentials are never persisted as repository identity.

### 6.3 Repository versions

A repository version represents one immutable base state.

Contains:

- repository-version identity;
- repository identity;
- source revision;
- content digest;
- snapshot identity;
- parent repository version, when meaningful;
- creation reason;
- created timestamp;
- index compatibility metadata;
- current/historical state.

### 6.4 Workspace versions

A workspace version represents one ordered mutable state derived from a repository version.

Contains:

- workspace-version identity;
- repository identity;
- base repository-version identity;
- parent workspace version;
- version sequence;
- mutation-set identity;
- created timestamp;
- synchronization state;
- current/historical state.

### 6.5 Current pointers

The repository record may maintain materialized pointers to:

- current repository version;
- current workspace version;
- current index generation.

Pointer updates must be transactional with version-journal commits.

---

## 7. Version journal

The version journal records how repository state evolved.

### 7.1 Journal entry classes

Journal entries include:

- repository version created;
- workspace version created;
- file created;
- file modified;
- file deleted;
- file renamed;
- configuration changed;
- evidence invalidated;
- incremental refresh completed;
- full rebuild completed;
- current index advanced;
- index schema migrated.

### 7.2 Journal entry fields

A journal entry contains:

- journal identity;
- repository identity;
- repository version;
- prior workspace version;
- resulting workspace version;
- journal entry type;
- causal operation;
- mutation or refresh payload;
- timestamp;
- content hashes;
- affected index generations.

### 7.3 Journal ordering

Journal entries are totally ordered within one repository.

### 7.4 Journal and current index consistency

The current index may advance only when:

- updated index data is committed;
- journal entry is committed;
- current workspace-version pointer is updated.

These changes occur atomically.

### 7.5 Historical reconstruction

The initial architecture does not require arbitrary live queries against every historical version.

The journal supports:

- provenance;
- stale-evidence analysis;
- audit;
- comparison;
- snapshot reconstruction where source artifacts exist.

Periodic snapshots may be added later.

---

## 8. Repository intelligence domain

The repository intelligence domain stores the mutable current index.

### 8.1 Current index contents

The current index may include:

- files;
- file hashes;
- symbols;
- signatures;
- source ranges;
- imports;
- references;
- call relationships;
- ownership relationships;
- summaries;
- alternate representations;
- lexical search indexes;
- full-text indexes;
- embeddings;
- index diagnostics.

### 8.2 Index scope

Every indexed record is scoped to:

- repository identity;
- active repository version;
- active workspace version or index generation.

### 8.3 Index generation

An index generation identifies one committed materialized index state.

Contains:

- index-generation identity;
- repository identity;
- repository version;
- workspace version;
- schema version;
- configuration identity;
- build mode;
- created timestamp;
- current flag;
- consistency status.

### 8.4 Mutable index strategy

Kiln uses a mutable current index plus journal rather than full row duplication per version.

The index may be updated through:

- row replacement;
- delete-and-insert for changed files;
- relation recomputation;
- representation replacement;
- FTS updates;
- embedding updates.

### 8.5 Atomic refresh

A refresh must not expose partial results as current.

Possible implementation strategies include:

- transactionally replacing affected rows;
- staging rows under a pending generation;
- committing a generation pointer after all work succeeds.

The exact SQL strategy remains an implementation detail.

### 8.6 Invalidated evidence

Invalidated evidence is represented explicitly.

Possible states:

- current;
- stale;
- refreshing;
- unavailable;
- historical.

A stale record cannot be returned as current evidence.

### 8.7 Index reuse

A current index may be reused when:

- repository identity matches;
- content digest or revision matches;
- workspace version matches;
- index schema is compatible;
- language and ignore configuration are compatible;
- required retrieval features are available.

---

## 9. File and symbol identity

### 9.1 File identity

A file identity is stable within one repository version and workspace lineage where possible.

It should not be based only on row identity.

Possible inputs include:

- repository identity;
- normalized path;
- content digest;
- lineage metadata.

### 9.2 Symbol identity

A symbol identity should incorporate:

- repository identity;
- file identity;
- qualified name;
- semantic kind;
- stable source locator or digest.

### 9.3 Rename handling

File and symbol rename detection may preserve lineage while producing new current identities.

The version journal records the relationship.

### 9.4 Identity stability

Identity stability is required within a committed index generation.

Cross-version stability is best effort unless explicitly guaranteed by the candidate contract.

---

## 10. Runtime domain

The runtime domain stores materialized state for runs.

### 10.1 Runs

A run record contains:

- run identity;
- installation or tenant scope;
- immutable run specification;
- lifecycle state;
- lifecycle-state version;
- current turn;
- base repository version;
- current workspace version;
- repository-session metadata;
- created, started, and ended timestamps;
- terminal state and stop reason;
- final-result reference.

### 10.2 Run specification

The full run specification may be:

- stored inline when bounded;
- stored as an artifact with indexed summary fields.

Indexed fields include:

- repository identity;
- task identity or hash;
- model;
- policy;
- security profile;
- validation requirement.

### 10.3 Run state

Materialized run state includes:

- lifecycle state;
- current turn;
- task-state version;
- context-state version;
- budget state;
- capability state;
- pending operation;
- recovery ownership;
- terminal result.

### 10.4 Task state

Task state may include:

- current objective;
- current plan;
- completed steps;
- unresolved questions;
- proposed output;
- structured constraints.

Large free-form task content may be artifact-backed.

### 10.5 Context state

Context persistence includes:

- context-item identity;
- candidate identity;
- lifecycle class;
- active representation;
- admission reason;
- first-seen turn;
- last-used turn;
- pin state;
- repository and workspace versions;
- estimated token cost;
- stale/current status.

### 10.6 Budget state

Budget persistence includes:

- configured limits;
- committed usage;
- reserved usage;
- remaining usage;
- exhaustion state;
- estimate-versus-actual metrics.

### 10.7 Capability state

Capability persistence includes:

- capability grant identity;
- type;
- scope;
- target;
- source of authority;
- expiration;
- revocation state.

Secrets and raw credentials are not persisted in capability records.

### 10.8 Operations

Operation records include:

- operation identity;
- run identity;
- operation type;
- state;
- attempt number;
- causal operation;
- correlation identity;
- authorization reference;
- budget reservation reference;
- start and end timestamps;
- outcome.

---

## 11. Event domain

The event domain stores immutable ordered events.

### 11.1 Run event stream

Each event contains:

- event identity;
- run identity;
- run sequence;
- event type;
- event schema version;
- occurred timestamp;
- producer;
- structured payload;
- causation identity;
- correlation identity;
- operation identity;
- artifact references.

### 11.2 Event ordering

Run sequence is unique and monotonically increasing within one run.

### 11.3 Event immutability

Committed events are not updated.

Correction or supersession uses a new event.

### 11.4 Event indexing

The event domain should support indexes by:

- run identity and sequence;
- event type;
- operation identity;
- turn identity;
- correlation identity;
- repository identity;
- timestamp;
- terminal status.

### 11.5 Event retention

Event metadata may outlive artifact blobs.

Event deletion follows explicit run or installation retention policy.

---

## 12. Artifact domain

Artifacts are stored as blobs in the database.

### 12.1 Artifact metadata

An artifact contains:

- artifact identity;
- installation or tenant scope;
- run identity, when applicable;
- repository or validation scope, when applicable;
- artifact kind;
- content type;
- content hash;
- uncompressed size;
- stored size;
- compression;
- blob bytes;
- creation timestamp;
- retention class;
- deletion state.

### 12.2 Artifact kinds

Examples:

- run specification;
- repository snapshot;
- candidate batch;
- rendered model request;
- model response;
- provenance map;
- patch;
- command output;
- test report;
- validation request;
- validation report;
- final answer;
- final result;
- error detail.

### 12.3 Content addressing

Artifacts should support content-hash lookup.

Physical blob bytes may be deduplicated.

Logical artifact references remain distinct when required for provenance.

### 12.4 Compression

Artifacts may be compressed before storage.

Metadata records:

- compression algorithm;
- original size;
- stored size;
- content hash of canonical uncompressed content.

### 12.5 Size limits

The persistence layer must enforce:

- maximum single-artifact size;
- maximum per-run artifact total;
- maximum installation database size or warning threshold.

An artifact exceeding policy may be rejected or require alternate storage in future hosted deployments.

### 12.6 Artifact integrity

Artifact reads verify:

- artifact identity;
- scope;
- expected content hash;
- stored-byte integrity where supported.

### 12.7 Artifact deletion

Artifact deletion may be:

- physical;
- logical tombstone;
- deferred garbage collection.

Events referencing deleted artifacts remain immutable.

---

## 13. Validation domain

Validation persistence is shared through core contracts while validation remains a separate package.

### 13.1 Validation request

A validation request contains:

- validation identity;
- run identity;
- base repository version;
- source snapshot reference;
- patch artifact reference;
- changed-file manifest;
- validation profile;
- security profile;
- budgets;
- creation timestamp.

Validation inputs are immutable after the run enters `validating`.

### 13.2 Validation attempts

Each attempt contains:

- attempt identity;
- validation identity;
- validator identity;
- state;
- start and end timestamps;
- interruption state;
- budget usage;
- error information.

### 13.3 Validation report

A report contains:

- validation identity;
- status;
- patch applicability;
- check summaries;
- policy outcomes;
- security outcomes;
- publication eligibility;
- approval requirement;
- report artifact reference.

### 13.4 Recovery

`validating` recovery uses the immutable request.

A new validation attempt may be created after interruption.

---

## 14. Transaction boundaries

The following changes should be atomic.

### 14.1 Lifecycle transition

Commit together:

- run lifecycle state;
- lifecycle-state version;
- primary lifecycle event;
- terminal reason when applicable.

### 14.2 Budget mutation

Commit together:

- reservation or usage ledger change;
- materialized budget state;
- budget event.

### 14.3 Context mutation

Commit together:

- context-item lifecycle changes;
- context-state version;
- context events.

### 14.4 Capability decision

Commit together:

- capability decision record;
- grant use or denial state;
- capability event.

### 14.5 Workspace mutation

Commit together:

- workspace-version creation;
- mutation journal entries;
- stale-evidence marks;
- workspace mutation event;
- current workspace pointer advancement.

File-system mutation itself may require a coordinated external transaction pattern because the filesystem and database are separate resources.

### 14.6 Repository refresh

Commit together:

- updated current-index rows or generation;
- refresh journal entry;
- stale-state changes;
- current index-generation pointer;
- refresh completion event.

### 14.7 Artifact creation

Commit together:

- artifact metadata;
- artifact blob bytes;
- artifact-created event or pending event reference.

### 14.8 Validation request creation

Commit together:

- immutable validation request;
- referenced artifact validation;
- transition to `validating`;
- validation-request event.

---

## 15. Filesystem and database coordination

Workspace files live outside the installation database.

This creates a dual-resource consistency problem.

### 15.1 Mutation protocol

A safe mutation sequence is:

```text
authorize mutation
    ↓
record mutation intent
    ↓
apply filesystem change
    ↓
verify resulting content hash
    ↓
create new workspace version
    ↓
invalidate evidence
    ↓
commit mutation outcome
```

### 15.2 Indeterminate mutations

If the runtime crashes after changing the filesystem but before committing the database outcome, recovery must detect divergence.

Detection uses:

- mutation intent;
- expected prior digest;
- expected new digest;
- current filesystem digest;
- operation state.

### 15.3 Reconciliation

Reconciliation may:

- complete the database commit;
- roll back the filesystem change if possible;
- create a new externally modified workspace version;
- mark the run failed and require repository refresh.

### 15.4 Initial milestone

The first read-only milestone does not require filesystem mutation coordination.

---

## 16. Concurrency model

### 16.1 Multiple runs

Multiple runs may share one installation database.

### 16.2 Shared repositories

Multiple read-only runs may use the same current repository index.

### 16.3 Writer serialization

Concurrent writes to one repository workspace require coordination.

Possible policy:

- one active workspace writer per repository;
- multiple concurrent readers;
- validation uses immutable snapshots.

### 16.4 Run isolation

Every run-scoped query includes or inherits run scope.

Cross-run mutation of run state is prohibited.

### 16.5 Repository-session isolation

Repository sessions bind:

- run;
- repository;
- repository version;
- workspace version;
- allowed operations.

### 16.6 Database write contention

The runtime should minimize long-lived write transactions.

Large parsing or model operations occur outside database write transactions.

### 16.7 Leases

Runtime ownership and recovery may use persisted leases.

A lease contains:

- owner runtime-session identity;
- acquired timestamp;
- expiry or heartbeat;
- recovery generation.

---

## 17. Recovery model

### 17.1 Runtime startup scan

On startup, the runtime scans for:

- non-terminal runs;
- stale runtime-session leases;
- interrupted operations;
- incomplete migrations;
- incomplete repository refreshes;
- incomplete validation attempts.

### 17.2 Recoverable run states

The initial architecture recovers:

- `preparing_repository`;
- `validating`.

### 17.3 Non-recoverable run states

Interrupted runs in these states fail:

- `created`, unless still owned by active submitter;
- `initializing`;
- `running`;
- `producing_output`.

### 17.4 Repository preparation recovery

Recovery uses:

- preparation checkpoints;
- index-generation state;
- journal state;
- committed file and symbol data;
- worker restart.

Incomplete transactions are rolled back automatically by the database.

### 17.5 Validation recovery

Recovery uses:

- immutable validation request;
- input artifact hashes;
- prior attempt state;
- new attempt identity.

### 17.6 Orphaned reservations

Startup reconciliation identifies budget reservations whose operations did not complete.

Each reservation is:

- committed if actual usage is known;
- released if operation did not start;
- marked indeterminate and resolved by policy otherwise.

### 17.7 Orphaned sessions

Transient repository and worker sessions are marked closed or expired.

Persisted logical repository state remains.

---

## 18. Retention

### 18.1 Retention classes

Suggested retention classes:

- ephemeral;
- run default;
- audit;
- security;
- user pinned.

### 18.2 Run deletion

Deleting a run may remove:

- materialized run state;
- run events;
- run-private artifacts;
- validation records.

Shared repository index data remains unless separately removed.

### 18.3 Artifact retention

Artifacts may expire before event metadata.

Events then retain:

- artifact identity;
- content hash;
- original metadata;
- deletion status.

### 18.4 Repository cleanup

Unused repository state may be removed based on:

- last access;
- active run references;
- pinned status;
- source availability;
- user policy.

### 18.5 Journal retention

Version journals should be retained long enough to support:

- stale-evidence analysis;
- recovery;
- audit;
- index consistency.

Journal compaction must preserve required provenance.

---

## 19. Garbage collection

Garbage collection may remove:

- unreferenced artifact blobs;
- expired ephemeral artifacts;
- abandoned preparation checkpoints;
- obsolete non-current index staging data;
- expired runtime-session records;
- old diagnostics;
- unreferenced repository snapshots.

### 19.1 Reference safety

A blob is physically deleted only when no retained logical reference requires it.

### 19.2 GC events

Garbage collection records:

- collection run;
- selected policy;
- reclaimed bytes;
- deleted artifact identities;
- retained exceptions;
- errors.

### 19.3 Compaction

Database compaction is a maintenance operation distinct from logical deletion.

---

## 20. Migrations

### 20.1 Schema version

The installation database records one schema version.

### 20.2 Migration ownership

Only one runtime or migration process may perform schema migration.

### 20.3 Migration lock

Migration requires exclusive ownership.

Other runtime processes must refuse normal operation or remain read-only during migration.

### 20.4 Migration atomicity

Where possible, one migration step commits atomically.

Long migrations may use checkpoints.

### 20.5 Compatibility

The runtime declares supported database schema versions.

Unsupported newer schema versions are rejected.

### 20.6 Index migrations

Repository index-schema migration may:

- transform current index;
- mark representations stale;
- require full rebuild;
- preserve version journal.

---

## 21. Backup and export

### 21.1 Database backup

A backup should capture a consistent database snapshot.

### 21.2 Run export

A run export may include:

- run specification;
- events;
- artifacts;
- final result;
- repository and workspace version metadata;
- validation report.

### 21.3 Repository export

A repository export may include:

- registration metadata;
- current index metadata;
- version journal;
- optional source snapshot.

### 21.4 Import

Import validates:

- schema version;
- content hashes;
- scope conflicts;
- identity collisions;
- artifact integrity.

---

## 22. Security

### 22.1 Database permissions

The installation database should be readable and writable only by the owning user or service identity.

### 22.2 Secrets

Secrets must not be stored in:

- events;
- artifact blobs;
- repository metadata;
- capability grants;
- model request artifacts.

### 22.3 Sensitive artifacts

Sensitive artifacts require scoped access checks.

### 22.4 Encryption

Local encryption-at-rest may depend on operating-system and storage configuration initially.

Hosted deployments should use managed encryption and tenant-specific controls.

### 22.5 Scoped access

Components receive restricted persistence views.

Examples:

- repository worker accesses repository-index domains but not model artifacts;
- validator accesses only its validation request and referenced inputs;
- publisher accesses only validated publication artifacts;
- Python SDK accesses run-facing APIs rather than raw database handles.

### 22.6 No public SQL interface

Kiln does not expose a generic SQL endpoint to plugins, workers, or users through the runtime API.

---

## 23. Performance considerations

### 23.1 Shared database benefits

One installation database allows:

- index reuse;
- shared FTS infrastructure;
- centralized migrations;
- cross-run inspection;
- centralized retention;
- deduplicated artifacts.

### 23.2 Blob growth

Database-backed artifacts may cause rapid file growth.

Kiln should support:

- compression;
- deduplication;
- size reporting;
- retention;
- GC;
- compaction;
- export and purge.

### 23.3 Event volume

High-volume events should remain structured and bounded.

Large payloads remain artifact-backed.

### 23.4 Index access

Repository queries should use scoped indexes including repository identity and current generation.

### 23.5 Long operations

Parsing, inference, validation, and compression occur outside long database write transactions.

---

## 24. Local and hosted mapping

### 24.1 Local

```text
One user installation
    └── one kiln.db
          ├── many repositories
          ├── many runs
          ├── current indexes
          ├── journals
          ├── events
          └── artifact blobs
```

### 24.2 Hosted

Possible physical mappings:

```text
Tenant
    └── dedicated database
```

or:

```text
Execution domain
    └── ephemeral database
```

or:

```text
Control plane database
    +
object storage for artifact bytes
```

The logical contracts remain the same.

### 24.3 Isolation warning

One shared database file provides logical isolation, not sufficient hostile multi-tenant isolation by itself.

---

## 25. Initial vertical-slice persistence

The first read-only milestone requires these domains.

### 25.1 Required installation data

- installation identity;
- schema version;
- runtime session.

### 25.2 Required repository data

- workspace;
- repository;
- repository version;
- workspace version;
- index generation;
- files;
- symbols;
- one relation family;
- source representations;
- preparation checkpoints.

### 25.3 Required run data

- run specification;
- run state;
- task state;
- context items;
- budget state;
- capability grants;
- operations;
- final result.

### 25.4 Required events

All events required by the first milestone in `events.md`.

### 25.5 Required artifacts

- run specification when large;
- repository candidate batches when large;
- rendered model requests;
- model responses;
- provenance maps;
- final answer;
- final result;
- error details.

### 25.6 Required recovery

- resume repository preparation;
- fail interrupted running state;
- release or reconcile orphaned reservations;
- expire transient repository sessions.

### 25.7 Explicitly deferred

- workspace mutation persistence;
- patch storage;
- validation records;
- publication records;
- historical index snapshots;
- hosted tenant partitioning;
- external object storage.

---

## 26. Persistence invariants

1. The default local topology is one database per user installation.
2. Every persisted object belongs to an explicit logical scope.
3. Public APIs do not expose unscoped raw database access.
4. Repository indexes are scoped by repository and active generation.
5. Kiln uses a mutable current index plus version journal.
6. The current index never exposes partial refresh results as current.
7. Version-journal and current-pointer advancement commit atomically.
8. Events are immutable.
9. Materialized state and event history remain logically separate.
10. Lifecycle transition and primary lifecycle event commit atomically.
11. Budget ledger changes and budget events commit atomically.
12. Context mutations and context events commit atomically.
13. Workspace-version advancement and invalidation commit atomically.
14. Validation inputs are immutable before `validating`.
15. Artifacts are stored as database blobs in the local default.
16. Artifact metadata includes content hash and size.
17. Artifact deletion does not rewrite prior events.
18. Secrets are not persisted.
19. Cross-run state access is rejected.
20. Cross-repository access is constrained by scoped sessions.
21. Long-running external work does not hold database write transactions open.
22. Recoverable operations persist checkpoints.
23. Interrupted `running` and `producing_output` runs fail.
24. Interrupted `preparing_repository` and `validating` runs may recover.
25. Only one runtime owns or recovers a non-terminal run.
26. Schema migrations are exclusively owned and versioned.
27. Logical deletion and physical garbage collection are distinct.
28. Shared blob deduplication preserves logical artifact references.
29. Database size and artifact growth are observable.
30. Hosted deployments may change physical topology without changing logical contracts.

---

## 27. Open persistence questions

The persistence model is sufficient for implementation planning. Remaining details include:

- exact table layout;
- exact identity formats;
- exact Turso/libSQL feature usage;
- whether artifact blobs use a separate table or shared content-addressed blob table;
- compression algorithm defaults;
- default size thresholds;
- exact writer-locking strategy;
- exact runtime-session lease duration;
- repository index generation implementation;
- full-text and vector index organization;
- migration tooling;
- backup cadence;
- retention defaults;
- journal compaction strategy;
- maximum recommended installation database size;
- when local deployments should warn or offer external artifact storage.

These questions do not change the core persistence semantics.
