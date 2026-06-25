# Kiln Architecture

## Status

Draft

## Purpose

This document defines the architectural boundaries, component responsibilities, control flow, trust model, persistence model, and runtime lifecycle for Kiln.

It does not define implementation details such as package names, concrete types, database schemas, wire encodings, or provider-specific APIs. Those should follow from the contracts described here.

Kiln is a secure, budget-aware runtime for repository-scale software engineering tasks performed with AI models.

A Kiln run accepts:

- a repository;
- a task;
- a model;
- a context policy;
- a security profile;
- resource budgets;
- optional validation requirements;

and produces:

- a final answer;
- an optional patch;
- test and validation results;
- an auditable execution trace;
- a terminal stop reason;
- optional publication artifacts.

---

# 1. Architectural principles

Kiln is built around the following principles.

## 1.1 The runtime is authoritative

The model may propose actions, but it does not own execution state, permissions, budgets, or termination.

The runtime decides:

- what context enters a model request;
- whether a tool may run;
- whether a repository operation is valid;
- whether a budget can be spent;
- whether a result is complete;
- whether an output is eligible for validation or publication.

## 1.2 Repository evidence is structured

Repository content is not passed around as anonymous strings.

Every repository result is represented as structured evidence with:

- stable identity;
- repository revision;
- workspace version;
- provenance;
- semantic kind;
- source location;
- representation level;
- estimated cost;
- relevance metadata;
- alternative representations.

## 1.3 Retrieval and context admission are separate

The repository engine retrieves evidence.

The context policy evaluates evidence.

The context manager decides what is active.

The renderer produces model input.

Retrieving an item does not imply that the model sees it.

## 1.4 Effects require explicit capabilities

No component receives ambient authority.

Repository writes, process execution, network access, model invocation, external integrations, artifact publication, and credential use are separately authorized capabilities.

## 1.5 Model output is untrusted

Model output is always treated as a proposal.

It may request:

- more evidence;
- a tool call;
- a file mutation;
- a test run;
- task completion.

The runtime validates every request before acting.

## 1.6 Repository content is untrusted

Source files, comments, documentation, configuration, test fixtures, generated code, and external issue content may contain instructions intended to influence the model.

Repository content is evidence, not authority.

## 1.7 Every important decision is observable

Kiln records enough information to reconstruct:

- what the model saw;
- what evidence was retrieved;
- what context was admitted;
- what operations were requested;
- what operations were allowed or denied;
- what budgets were consumed;
- what files changed;
- why the run stopped.

## 1.8 Validation is independent

The agent may run tests during execution, but final validation is a separate subsystem and package that shares Kiln's core contracts.

A model or agent cannot declare its own output safe for publication.

## 1.9 Embedded ownership does not imply a single process

The public product behaves as an embedded Python library, but the authoritative Go runtime executes as a privately supervised child process.

Risky or extensible components may run in additional isolated workers.

## 1.10 Repository state is versioned

Every repository candidate is tied to a repository version and workspace version.

Workspace mutations synchronously invalidate affected evidence. Stale evidence cannot silently re-enter active context as current evidence.

---

# 2. System context

Kiln has four primary architectural domains.

```text
Developer or external workflow
            │
            ▼
Product interface
Python SDK · CLI · hosted API
            │
            ▼
Runtime control plane
Agent loop · context · budgets · capabilities
       │             │             │
       ▼             ▼             ▼
Repository       Model system   Workspace tools
intelligence
            │
            ▼
State, events, artifacts
            │
            ▼
Validation and optional publication
```

The runtime control plane is the authoritative center of the system.

---

# 3. Major components

## 3.1 Product interface

The product interface converts developer intent into a normalized run specification.

Possible interfaces include:

- Python SDK;
- command-line interface;
- hosted HTTP API;
- workflow trigger;
- notebook client;
- CI integration.

### Consumes

- repository reference;
- task description;
- model configuration;
- context policy;
- security profile;
- budgets;
- validation requirements;
- metadata.

### Produces

- validated run specification;
- run identifier;
- event stream;
- final result handle.

### Does not own

- context selection;
- tool authorization;
- model provider behavior;
- repository parsing;
- validation policy.

---

## 3.2 Runtime process supervisor

The Python SDK privately supervises the Go runtime as a child process.

### Consumes

- runtime binary location;
- runtime configuration;
- run requests;
- cancellation requests.

### Produces

- private runtime channel;
- runtime health state;
- streamed events;
- runtime results;
- lifecycle control.

### Responsibilities

- start the runtime without creating a public listening port;
- establish a private pipe, socket pair, Unix socket, or named pipe;
- authenticate the runtime relationship through process ownership and session identity;
- terminate the runtime when the owning SDK session closes;
- detect unexpected runtime exit;
- propagate cancellation;
- prevent unrelated local processes from submitting run commands.

The Python SDK presents an embedded API even though execution occurs in a separate process.

---

## 3.3 Run coordinator

The run coordinator owns the lifecycle of one run.

It creates the run, initializes dependencies, supervises execution, handles cancellation, and produces the final result.

### Consumes

- run specification;
- available adapters;
- repository reference;
- runtime configuration.

### Produces

- initialized run state;
- component sessions;
- lifecycle events;
- terminal run result.

### Responsibilities

- assign run identity;
- initialize state;
- open the repository session;
- initialize budgets;
- establish capabilities;
- start the agent loop;
- coordinate shutdown;
- recover interrupted runs only from `preparing_repository` and `validating`;
- mark interruptions in other active states as terminal failures;
- assemble final artifacts;
- assign one terminal stop reason.

---

## 3.4 Agent loop

The agent loop is the repeated reasoning and action cycle.

### Consumes

- task state;
- active context;
- conversation state;
- budget state;
- available tool descriptions;
- model responses;
- tool results;
- repository results.

### Produces

- context-planning requests;
- model requests;
- repository requests;
- tool requests;
- workspace mutation proposals;
- completion proposals;
- state transitions.

### Core cycle

```text
Read current state
    ↓
Plan next context
    ↓
Render model request
    ↓
Invoke model
    ↓
Interpret model response
    ↓
Perform approved operation
    ↓
Update state
    ↓
Evaluate stop conditions
```

The loop does not directly access the filesystem, invoke external models, or execute commands.

---

## 3.5 Task state manager

The task state manager tracks structured task progress independently of message history.

### Consumes

- original task;
- task constraints;
- model outputs;
- tool outcomes;
- validation outcomes.

### Produces

- current objective;
- current plan;
- completed steps;
- unresolved questions;
- proposed changes;
- final task summary.

The task state should remain compact and structured where possible.

---

## 3.6 Context manager

The context manager owns the lifecycle of all information that may be shown to the model.

### Context classes

- **Pinned**: system instructions, task, security constraints.
- **Available**: retrieved but not admitted.
- **Active**: included in the next model request.
- **Observed**: previously shown to the model.
- **Compressed**: lower-cost replacement for prior content.
- **Evicted**: removed from active context but retained in runtime state.
- **Transient**: short-lived tool output or diagnostics.
- **Stale**: evidence invalidated by a later repository or workspace version.

### Consumes

- context candidates;
- tool-result candidates;
- context plans;
- token estimates;
- conversation state;
- model context limits;
- repository-version validity information.

### Produces

- active context set;
- context transitions;
- rendered-input source set;
- provenance map;
- context usage events.

The context manager is authoritative about what the model actually sees.

---

## 3.7 Context policy engine

The context policy decides what evidence is worth retrieving, admitting, compressing, preserving, or evicting.

### Consumes

- task state;
- current turn;
- remaining budgets;
- active context;
- observed context;
- available candidates;
- relevance metadata;
- graph metadata;
- model reflection signals.

### Produces

A declarative context plan containing actions such as:

- retrieve;
- admit;
- reject;
- compress;
- replace;
- evict;
- preserve;
- pin;
- defer.

Policies may propose retrieval, but the runtime performs it.

A policy cannot:

- query the repository database directly;
- call the repository worker directly;
- mutate active context;
- spend budget;
- bypass revision or workspace-version checks.

A retrieval proposal follows this sequence:

```text
Policy proposes retrieval
        ↓
Runtime validates budget and repository scope
        ↓
Runtime performs repository request
        ↓
Policy receives structured candidates
        ↓
Policy proposes admission or rejection actions
```

The runtime validates every plan before applying it.

---

## 3.8 Context renderer

The context renderer converts active structured state into provider-neutral model messages.

### Consumes

- active context items;
- task state;
- conversation state;
- tool definitions;
- model capabilities;
- rendering rules.

### Produces

- ordered model messages;
- model-visible tool definitions;
- estimated token count;
- provenance mapping from rendered content to content identities.

The renderer decides presentation, not selection.

---

## 3.9 Budget manager

The budget manager tracks, reserves, commits, reconciles, and denies resource usage.

### Budget domains

- input tokens;
- output tokens;
- model calls;
- tool calls;
- repository queries;
- elapsed time;
- monetary cost;
- command execution time;
- output size;
- context duplication or churn.

### Consumes

- configured limits;
- repository-engine candidate estimates;
- provider-specific rendered-input counts;
- provider-reported actual usage;
- elapsed time;
- proposed context plans;
- proposed model calls;
- proposed tool calls.

### Produces

- budget reservations;
- committed usage;
- released reservations;
- remaining budget;
- denial decisions;
- exhaustion signals;
- estimation-error metrics.

### Token accounting model

Kiln uses a three-stage token model:

```text
Repository engine
    estimates candidate representation cost
        ↓
Model gateway
    performs provider-specific final preflight counting
        ↓
Budget manager
    reconciles estimates with actual provider usage
```

The runtime records:

- candidate-estimated tokens;
- rendered-request estimated tokens;
- provider-counted or provider-reported input tokens;
- actual output tokens.

### Reservation lifecycle

```text
Estimate
  ↓
Reserve
  ↓
Perform operation
  ↓
Commit actual usage
  ↓
Release unused reservation
```

No operation should begin if the runtime cannot reserve enough budget to complete it safely.

---

## 3.10 Model gateway

The model gateway is the provider-neutral model boundary.

### Consumes

- rendered model request;
- approved model configuration;
- model capability information;
- output budget reservation;
- credentials through a controlled broker.

### Produces

- normalized model response;
- proposed tool calls;
- generated text;
- provider-specific token count;
- actual usage;
- provider metadata;
- normalized errors.

The model gateway does not control context selection or tool authority.

---

## 3.11 Model egress controller

The model egress controller decides what repository and task data may leave the environment.

### Consumes

- rendered model request;
- content provenance;
- provider identity;
- security profile;
- excluded paths;
- secret-scan results;
- egress limits.

### Produces

- allow;
- deny;
- redact;
- require approval;
- egress audit event.

The controller must make it possible to answer:

- what content was sent;
- to which provider;
- under which policy;
- at what token and byte cost;
- whether protected paths contributed.

---

## 3.12 Repository session manager

The repository session manager binds the run to one repository identity, repository version, and workspace version.

### Consumes

- repository path or snapshot;
- expected revision;
- indexing configuration;
- repository security scope;
- workspace mutations.

### Produces

- repository session identity;
- pinned repository version;
- current workspace version;
- repository metadata;
- index readiness;
- revision-bound and version-bound request channel;
- stale-evidence notifications.

The repository worker should expose scoped sessions rather than generic queries over arbitrary repository identifiers.

```text
repository.open(repository_version_id, workspace_version_id)
    → repository_session_id

repository.search(repository_session_id, query)
```

A repository session carries:

- repository identity;
- repository version;
- workspace version;
- run identity;
- allowed operations.

---

## 3.13 Repository consistency and refresh manager

The consistency manager coordinates invalidation, incremental refresh, and full rebuilds.

These mechanisms are complementary rather than mutually exclusive.

### Mandatory invalidation

Every workspace mutation immediately invalidates affected derived evidence, including:

- file contents;
- symbols;
- signatures;
- summaries;
- embeddings;
- outgoing relations;
- incoming relations whose resolution may be affected;
- cached representations.

Invalidation is synchronous with the mutation.

```text
Workspace mutation
    ↓
Workspace version advances
    ↓
Affected evidence becomes stale
    ↓
Mutation completes
```

### Incremental refresh

Incremental refresh is the normal path when:

- a bounded number of files changed;
- parser and index semantics support partial replacement;
- the repository identity remains stable;
- graph effects can be recomputed safely.

### Full rebuild

A full rebuild is required or preferred when:

- the repository revision changes substantially;
- ignore or language configuration changes;
- index schema changes;
- incremental consistency cannot be guaranteed;
- too many files changed;
- corruption is detected.

### Refresh timing modes

The runtime may support configurable timing preferences:

- **eager**: refresh immediately after each mutation;
- **lazy**: refresh before stale evidence is next requested;
- **batch**: refresh after a group of mutations;
- **rebuild**: discard and fully prepare a new index.

Correctness is not configurable:

- stale evidence may not be treated as current;
- all evidence used as current must match the active repository and workspace versions;
- final reasoning and validation require synchronized current evidence.

Recommended default:

```text
During active editing:
    lazy or batched incremental refresh

Before final reasoning or validation:
    synchronize all stale evidence

On schema, configuration, or revision discontinuity:
    full rebuild
```

---

## 3.14 Repository engine

The repository engine converts source code into structured, queryable repository evidence.

### Ingestion subsystem

Consumes:

- repository files;
- ignore rules;
- language configuration;
- repository-version metadata;
- workspace-version metadata.

Produces:

- file records;
- file hashes;
- parse jobs;
- indexing diagnostics.

### Language-analysis subsystem

Consumes:

- source files.

Produces:

- symbols;
- signatures;
- source ranges;
- imports;
- references;
- relationships;
- parse diagnostics.

### Graph subsystem

Consumes:

- symbols;
- imports;
- references;
- inferred relationships.

Produces:

- call graph;
- import graph;
- ownership hierarchy;
- relation confidence;
- unresolved relation records.

### Index subsystem

Consumes:

- files;
- symbols;
- graph edges;
- summaries;
- representations.

Produces:

- searchable repository database;
- retrieval indexes;
- repository-version metadata;
- workspace-version metadata;
- stale/current status.

### Retrieval subsystem

Consumes requests such as:

- search;
- get source;
- get file;
- expand graph;
- find callers;
- find callees;
- get summary;
- get representation.

Produces:

- structured repository candidates.

The repository engine does not decide what enters model context.

---

## 3.15 Shared persistence layer

Kiln uses one embedded Turso-compatible database per user installation. That database can hold multiple workspaces, repositories, repository versions, runs, and agents while preserving logical scope.

The default local topology is:

```text
~/.kiln/
├── kiln.db
└── runtime/
```

A workspace may contain lightweight local configuration, but the installation database is the canonical persistence layer. CI, container, and hosted deployments may override the database location while preserving the same logical schema.

### Persistence hierarchy

```text
Shared Kiln database
│
├── workspaces
│   └── registered local or hosted workspace
│
├── repositories
│   └── logical repository identity
│
├── repository_versions
│   └── immutable indexed revision or derived workspace state
│
├── workspace_versions
│   └── ordered mutable workspace states
│
├── repository intelligence
│   ├── files
│   ├── symbols
│   ├── relations
│   ├── representations
│   └── index status
│
├── runtime
│   ├── runs
│   ├── run state
│   ├── task state
│   ├── context items
│   ├── budget transactions
│   └── capability grants
│
├── audit
│   ├── events
│   └── artifact references
│
└── validation
    ├── validation runs
    └── validation reports
```

### Scope model

```text
workspace_id
    └── repository_id
          └── repository_version_id
                └── workspace_version_id
                      ├── indexed evidence
                      └── runs
```

Every repository-indexed record is scoped to at least a repository version. Mutable workspace-derived evidence is additionally scoped to a workspace version.

Every run pins:

- a base repository version;
- a current workspace version;
- a repository session;
- an allowed scope.

### Isolation model

The shared database provides logical isolation through runtime-controlled scoped sessions.

Callers do not issue arbitrary unscoped queries. The runtime opens a repository session, and subsequent operations inherit that scope.

For local use, one database may hold multiple projects.

For hosted multi-tenant use, the same logical schema may be deployed as:

- one database per tenant;
- one database per execution domain;
- or one database per runner.

A single shared file is not considered sufficient adversarial tenant isolation by itself.

### State materialization

Repository intelligence uses a mutable current index plus a version journal.

The current materialized index contains the active view used for retrieval:

```text
current files
current symbols
current relations
current representations
```

The version journal records how that state was reached:

```text
repository versions
workspace versions
file mutations
index refreshes
invalidation records
```

This avoids copying the full repository index for each workspace version while preserving provenance, invalidation history, and comparison against the base revision. Historical versions are not required to remain fully queryable in the initial architecture.

### Persistence categories

The database holds four logical categories:

1. **Current state** — what is true now.
2. **Event history** — what happened.
3. **Repository indexes** — what is known about the current repository state.
4. **Artifacts** — large immutable payloads stored as blobs.

Artifacts remain referenced by identity from events and domain records even though their bytes reside in the same database.

---

## 3.16 Repository candidate model

The repository candidate is the primary exchange unit between the repository engine and runtime.

A candidate contains:

- stable content identity;
- repository identity;
- repository version;
- workspace version;
- semantic kind;
- file path;
- qualified name;
- representation;
- content or artifact reference;
- estimated tokens;
- relevance metadata;
- graph metadata;
- alternative representations;
- provenance;
- stale/current status.

Possible representation levels include:

- repository summary;
- package summary;
- file summary;
- file outline;
- symbol signature;
- symbol summary;
- filtered source;
- full source;
- graph path;
- search result.

The repository engine estimates token cost for each candidate representation.

---

## 3.17 Capability broker

The capability broker is the runtime's authorization authority.

### Capability categories

- repository read;
- repository write;
- process execution;
- network connection;
- model invocation;
- external integration;
- artifact publication;
- credential use.

### Consumes

- requested operation;
- run identity;
- current grants;
- security profile;
- target resource;
- optional approval.

### Produces

- authorized operation;
- narrowed authority;
- denial;
- authorization event.

Capabilities do not imply one another.

```text
filesystem.write ≠ process.execute
process.execute ≠ network.connect
repository.read ≠ git.push
model.invoke ≠ arbitrary network access
```

---

## 3.18 Tool registry

The tool registry defines the operations the model may request.

### Consumes

- built-in tool definitions;
- approved extensions;
- security profile;
- model tool-call format.

### Produces

- model-visible tool descriptions;
- validated invocation requests;
- dispatch targets.

The registry defines availability.

The capability broker defines authority.

A registered tool may still be unavailable in a particular run.

---

## 3.19 Workspace manager

The workspace manager owns the mutable working tree.

### Conceptual model

```text
Immutable base snapshot
        +
Writable task overlay
        =
Current workspace
```

### Consumes

- repository snapshot;
- approved reads;
- approved writes;
- patch operations.

### Produces

- current workspace state;
- new workspace version;
- changed-file list;
- patch;
- file snapshots;
- invalidation requests.

The workspace manager does not expose Git credentials or repository remotes to the agent.

---

## 3.20 Command sandbox

The command sandbox runs approved development commands.

### Consumes

- executable;
- arguments;
- working directory;
- environment policy;
- timeout;
- CPU limit;
- memory limit;
- process limit;
- output limit;
- network policy.

### Produces

- exit status;
- bounded stdout;
- bounded stderr;
- structured diagnostics;
- generated artifacts;
- resource usage.

Commands should be structured.

Arbitrary shell expressions are not supported by default.

---

## 3.21 Tool result processor

The result processor converts raw results into structured candidates suitable for context planning.

### Consumes

- raw command output;
- repository results;
- diagnostics;
- changed-file state;
- output-size limits.

### Produces

Possible representations:

- full output;
- truncated output;
- failure summary;
- diagnostic list;
- changed-file summary;
- test summary;
- artifact reference.

Tool output never enters model context directly.

---

## 3.22 Event store

The event store records the authoritative execution history.

### Event categories

- run lifecycle;
- repository lifecycle;
- context lifecycle;
- budget lifecycle;
- model invocation;
- tool invocation;
- capability decisions;
- workspace mutation;
- validation;
- retry and failure.

### Event payload policy

Events store first-class facts describing what occurred.

Large content that was consumed, generated, transferred, or produced is stored as an artifact and referenced from the event.

Store inline:

- event type;
- run, turn, and operation identities;
- causation and correlation identities;
- status;
- usage;
- content identities;
- decision facts;
- hashes;
- artifact references.

Store by reference:

- full rendered prompts;
- full model responses;
- source snapshots;
- patches;
- complete command output;
- large context payloads;
- test logs;
- validation bundles.

### Consumes

- structured events from all components.

### Produces

- durable ordered event stream;
- replay source;
- audit trail;
- evaluation data;
- operational diagnostics.

The event stream should be sufficient to determine:

- what the model saw;
- what it requested;
- what was allowed;
- what changed;
- what resources were consumed;
- why execution stopped.

---

## 3.23 State store

The state store holds the current derived state of a run.

### Consumes

- validated state transitions.

### Produces

- current run snapshot;
- restart data;
- status queries.

### State examples

- current lifecycle state;
- current turn;
- active context;
- remaining budgets;
- capability grants;
- current repository version;
- current workspace version;
- pending operation;
- terminal status.

```text
Event store = what happened
State store = what is true now
Artifact store = large immutable outputs
```

These may share one embedded database initially while remaining logically distinct.

---

## 3.24 Artifact store

The artifact store holds large or binary outputs as database blobs in the installation database.

### Possible artifacts

- repository snapshot;
- index;
- patch;
- test logs;
- model transcript;
- context snapshots;
- validation report;
- provenance bundle;
- final answer.

### Produces

- immutable artifact reference;
- content hash;
- size;
- compression metadata;
- retention metadata;
- access metadata.

Artifacts should be content-addressed where practical so identical payloads can be deduplicated. The artifact subsystem must support compression, size limits, retention, garbage collection, export, and deletion. Hosted deployments may later replace blob storage with object storage behind the same artifact contract.

---

## 3.25 Stop controller

The stop controller determines whether the run should continue.

### Consumes

- task state;
- model completion proposal;
- budget state;
- error state;
- validation state;
- cancellation signal;
- policy constraints.

### Produces

- continue;
- retry;
- re-plan;
- validate;
- stop with reason.

### Stop classes

- successful;
- budget exhausted;
- policy denied;
- validation failed;
- model failed;
- tool failed;
- repository failed;
- cancelled;
- internal error.

The model may propose completion.

The runtime determines whether completion is accepted.

---

## 3.26 Validation package

Validation is a separate package sharing Kiln's core contracts. It executes out of process and does not depend on the internal agent loop.

### Integration contract

The run coordinator creates an immutable `ValidationRequest` after output production and receives a structured `ValidationReport`.

```text
Kiln runtime
    │ ValidationRequest
    ▼
Kiln validation process or service
    │ ValidationReport
    ▼
Kiln runtime
```

The validation request references persisted immutable inputs:

- run identity;
- base repository version or snapshot artifact;
- patch artifact;
- changed-file manifest;
- validation profile;
- security profile;
- validation budget.

The validator never receives the live agent workspace, model credentials, or publication credentials.

### Validation execution

The validation package:

1. creates a clean temporary workspace;
2. materializes the pinned base repository state;
3. verifies the snapshot hash and revision;
4. applies the proposed patch;
5. verifies the changed-file manifest;
6. runs required static checks, tests, and security checks;
7. stores large outputs as artifact blobs;
8. returns a structured validation report;
9. destroys the temporary workspace.

### Consumes

- immutable base repository version;
- proposed patch artifact;
- changed-file manifest;
- validation specification;
- security policy;
- artifact references.

### Produces

- patch applicability result;
- clean test result;
- policy violations;
- protected-path result;
- secret-scan result;
- publication eligibility;
- approval requirement;
- validation report artifact.

### Local and hosted execution

Locally, the Go runtime privately supervises a validation child process using the same private transport style as other workers. The worker receives only narrowly scoped access to the referenced request and artifacts.

Hosted deployments may execute the same contract through a remote build service such as an isolated task or build job. Transport changes, but `ValidationRequest` and `ValidationReport` semantics remain the same.

### Recovery

Validation is recoverable after runtime interruption because its inputs are immutable and persisted before the run enters `validating`. Recovery restarts validation from the existing request.

---

## 3.27 Publisher

The publisher is optional and remains outside the agent runtime.

### Consumes

- validated patch;
- publication approval;
- repository identity;
- base revision;
- pull-request metadata;
- short-lived publishing credential.

### Produces

- branch reference;
- commit identity;
- pull-request identity;
- publication event.

The publisher accepts validated publication requests, not free-form model instructions.

---

# 4. Core domain objects

The first architecture contracts should define the semantics of the following objects.

## Run specification

Declares the requested execution.

Contains:

- repository reference;
- task;
- model;
- policy;
- budgets;
- security profile;
- validation requirements;
- metadata.

## Run state

Represents the current execution state.

Contains:

- lifecycle state;
- current turn;
- task state;
- active context;
- budget state;
- capability grants;
- repository session;
- base repository version;
- current workspace version;
- pending operation;
- terminal result.

## Workspace

Represents one registered local or hosted working environment.

Contains:

- workspace identity;
- root location or snapshot identity;
- ownership or tenant scope;
- registered repositories;
- persistence scope.

## Repository

Represents a logical repository across revisions and workspace states.

Contains:

- repository identity;
- workspace identity;
- canonical source identity;
- name;
- metadata.

## Repository version

Represents one immutable indexed repository revision or derived repository state.

Contains:

- repository-version identity;
- repository identity;
- source revision;
- parent version;
- content digest;
- index status;
- creation reason.

## Workspace version

Represents one ordered mutable state of a workspace.

Contains:

- workspace-version identity;
- repository-version identity;
- parent workspace version;
- mutation set;
- stale evidence set;
- synchronization status.

## Repository session

Represents one scoped, revision-bound, workspace-version-bound repository view.

Contains:

- repository-session identity;
- run identity;
- repository identity;
- repository version;
- workspace version;
- allowed operations.

## Repository candidate

Represents evidence returned by the repository engine.

Contains:

- content identity;
- repository version;
- workspace version;
- semantic kind;
- file path;
- qualified name;
- representation;
- content or artifact reference;
- estimated tokens;
- relevance metadata;
- graph metadata;
- alternatives;
- provenance;
- stale/current status.

## Context item

Represents evidence tracked by the runtime.

Contains:

- candidate identity;
- lifecycle state;
- active representation;
- admission reason;
- first-seen turn;
- last-used turn;
- pin status;
- estimated cost;
- repository and workspace versions.

## Context plan

Declares proposed context transitions.

Contains actions such as:

- retrieve;
- admit;
- reject;
- compress;
- replace;
- evict;
- preserve;
- pin.

## Model request

Contains:

- ordered messages;
- tool definitions;
- model configuration;
- output limit;
- provenance references;
- budget reservation.

## Model response

Contains:

- generated content;
- tool proposals;
- estimated and actual usage;
- finish reason;
- provider metadata.

## Tool call

Contains:

- tool identity;
- structured arguments;
- requesting turn;
- required capabilities.

## Tool result

Contains:

- status;
- structured output;
- raw artifact references;
- diagnostics;
- usage;
- candidate representations.

## Capability grant

Contains:

- capability type;
- scope;
- target;
- expiration;
- source of authority;
- approval metadata.

## Budget state

Contains:

- configured limits;
- reserved usage;
- committed usage;
- remaining usage;
- exhaustion state;
- estimate-versus-actual metrics.

## Event

Contains:

- event identity;
- run identity;
- sequence;
- timestamp;
- event type;
- structured first-class facts;
- artifact references;
- causation identity;
- correlation identity.

## Artifact reference

Contains:

- artifact identity;
- content type;
- storage location;
- content hash;
- size;
- retention metadata;
- access scope.

## Validation report

Contains:

- patch applicability;
- test results;
- policy checks;
- security checks;
- approval requirement;
- publication eligibility.

## Run result

Contains:

- terminal status;
- stop reason;
- final answer;
- patch reference;
- validation reference;
- usage summary;
- event-stream reference;
- artifact references.

---

# 5. Canonical run lifecycle

## 5.1 Lifecycle states

```text
created
  ↓
initializing
  ↓
preparing_repository
  ↓
running
  ↓
producing_output
  ↓
validating
  ↓
completed
```

A run may transition from any non-terminal state to:

- failed;
- cancelled;
- exhausted.

## 5.2 State definitions

### Created

The run specification has been accepted and assigned an identity.

Required state:

- valid run specification;
- run ID;
- creation event.

### Initializing

The runtime is establishing:

- state storage;
- event storage;
- capability grants;
- budgets;
- adapters;
- deadlines.

### Preparing repository

The runtime is:

- resolving workspace and repository identity;
- pinning repository version;
- establishing workspace version;
- preparing snapshot;
- starting repository worker;
- loading or building index;
- opening a scoped repository session.

This state is recoverable. The coordinator resumes from the first incomplete idempotent preparation step. Partial index updates must commit atomically or be rolled back and repeated.

### Running

The agent loop is active.

Permitted operations include:

- context planning;
- model invocation;
- repository retrieval;
- approved tool execution;
- approved workspace mutation;
- repository invalidation and refresh.

### Producing output

The agent loop has proposed completion.

The runtime assembles:

- final answer;
- patch;
- changed-file list;
- provenance;
- execution summary.

### Validating

The output is evaluated by the separate validation package.

This state is recoverable. The runtime reconstructs the persisted `ValidationRequest` and restarts validation against the same immutable inputs.

### Completed

The run finished successfully.

### Failed

The run ended because of an unrecoverable component or internal error. An unexpected runtime interruption during `initializing`, `running`, or `producing_output` is recorded as `runtime_interrupted` and is not resumed in the initial architecture.

### Cancelled

The run ended because of an authorized cancellation request.

### Exhausted

The run ended because a hard resource limit was reached.

---

# 6. Canonical interaction sequences

## 6.1 Repository retrieval

```text
Agent loop or policy proposes repository retrieval
    ↓
Runtime validates budget and capability
    ↓
Repository session validates repository and workspace versions
    ↓
Repository engine performs query
    ↓
Repository engine returns candidates with estimated costs
    ↓
Runtime validates schema, scope, version, and limits
    ↓
Context policy evaluates candidates
    ↓
Context manager applies approved plan
    ↓
Renderer includes admitted items in a later model request
```

## 6.2 Model invocation

```text
Context policy proposes plan
    ↓
Runtime validates plan
    ↓
Context manager applies transitions
    ↓
Renderer builds provider-neutral messages
    ↓
Egress controller authorizes content
    ↓
Model gateway performs provider-specific token counting
    ↓
Budget manager reserves usage
    ↓
Model gateway invokes provider
    ↓
Budget manager commits and reconciles actual usage
    ↓
Normalized response returns to agent loop
```

## 6.3 Tool execution

```text
Model proposes tool call
    ↓
Tool registry validates tool and arguments
    ↓
Capability broker authorizes operation
    ├── denied → structured denial result
    ↓
Workspace or sandbox performs operation
    ↓
Result processor creates result candidates
    ↓
Context policy decides what reaches the model
    ↓
Events and artifacts are persisted
```

## 6.4 Workspace mutation and refresh

```text
Model proposes file change
    ↓
Tool schema validates target and content
    ↓
Capability broker checks write scope
    ↓
Workspace manager applies mutation
    ↓
Workspace version advances
    ↓
Consistency manager invalidates affected evidence
    ↓
Refresh policy selects eager, lazy, batch, or rebuild timing
    ↓
Repository engine refreshes before stale evidence is reused as current
    ↓
Patch and changed-file state are updated
```

## 6.5 Completion and validation

```text
Model proposes completion
    ↓
Stop controller checks task and budget state
    ↓
Runtime synchronizes stale repository evidence required for completion
    ↓
Runtime assembles output
    ↓
Workspace manager produces patch
    ↓
Validation package evaluates clean result
    ↓
Runtime records terminal result
    ↓
Optional publisher receives validated publication request
```

---

# 7. Communication boundaries

## 7.1 Python SDK to Go runtime

The Python SDK communicates with a privately supervised Go child process.

Preferred transports:

- inherited stdin and stdout;
- private socket pair;
- Unix domain socket;
- Windows named pipe.

Requirements:

- no public listening interface;
- one owning SDK session;
- explicit protocol version;
- request correlation;
- bounded messages;
- cancellation support;
- health detection;
- clean shutdown.

## 7.2 Trusted runtime components

These may communicate through direct in-process interfaces inside the Go runtime:

- run coordinator;
- agent loop;
- task state;
- context manager;
- built-in context policies;
- budget manager;
- capability broker;
- stop controller;
- event construction.

## 7.3 Isolated local workers

These should communicate through private typed protocols:

- Python repository engine;
- third-party Python policies;
- custom Python tools;
- local model workers;
- command workers.

Workers should not listen on public interfaces.

## 7.4 External services

External boundaries include:

- hosted API;
- remote model provider;
- object store;
- validation execution service;
- repository publisher.

These require explicit authentication, authorization, rate limiting, and tenant isolation.

---

# 8. Protocol families

Kiln should use separate protocols for separate trust boundaries.

## Runtime protocol

Used by the Python SDK or hosted interface.

Operations:

- run.create;
- run.cancel;
- run.status;
- run.events;
- run.result;
- runtime.health;
- runtime.close.

## Repository protocol

Used between the runtime and repository engine.

Operations:

- repository.open;
- repository.prepare;
- repository.search;
- repository.get_source;
- repository.expand_graph;
- repository.get_representation;
- repository.invalidate;
- repository.refresh;
- repository.close.

## Policy callback protocol

Used only for isolated non-native policies.

Operations:

- policy.describe;
- policy.plan;
- policy.close.

Policies may return retrieval proposals but cannot perform repository operations directly.

## Tool worker protocol

Used for approved external tools.

Operations:

- tool.describe;
- tool.execute;
- tool.cancel;
- tool.close.

## Model callback protocol

Used for Python-hosted or custom models.

Operations:

- model.capabilities;
- model.count_tokens;
- model.complete;
- model.cancel;
- model.close.

All protocols must be:

- typed;
- versioned;
- bounded in size;
- closed to unknown operations;
- correlated by request identity;
- validated at both ends.

---

# 9. Trust model

## Trusted

- Go runtime kernel;
- built-in policies;
- capability broker;
- budget manager;
- state transition logic;
- event store.

## Semi-trusted

- first-party repository engine;
- built-in model adapters;
- built-in tools;
- validation adapters.

## Untrusted

- repository contents;
- model output;
- tool output;
- generated code;
- external integrations;
- third-party Python packages;
- network responses;
- task-supplied content.

Untrusted data may influence reasoning but may not grant authority.

---

# 10. Required invariants

The following rules are architectural invariants.

1. Every model call requires an approved context plan.
2. Every model call requires a successful budget reservation.
3. Every remote model call requires egress authorization.
4. Every effectful operation requires a capability decision.
5. Repository results never enter model context directly.
6. Tool results never enter model context directly.
7. Model output never mutates runtime state directly.
8. All repository evidence is tied to a repository version and workspace version.
9. Evidence invalidated by a later mutation cannot be admitted as current until refreshed.
10. Historical or stale evidence must be explicitly labeled as such.
11. Workspace mutation synchronously advances workspace version and invalidates affected evidence.
12. Policies may propose retrieval, but only the runtime performs it.
13. Workers cannot register arbitrary runtime operations.
14. All state transitions emit events.
15. All terminal runs have exactly one stop reason.
16. Publication credentials never enter the agent runner.
17. Final validation is independent of the agent loop and implemented as a separate package.
18. Large payloads are stored as artifacts, not embedded in events.
19. Events store first-class facts sufficient to understand what happened.
20. The event stream records enough information to reconstruct model-visible context.
21. Denied operations are returned as structured results and recorded.
22. Capabilities are denied by default.
23. Capabilities are scoped and non-transitive.
24. The runtime remains authoritative even when policies or models are implemented in Python.
25. Repository-engine token estimates are advisory.
26. Provider-specific model-gateway counts are authoritative for preflight reservation.
27. Provider-reported actual usage is reconciled by the budget manager.
28. Shared persistence is accessed through scoped sessions rather than arbitrary unscoped identifiers.
29. Logical database isolation is not treated as sufficient adversarial multi-tenant isolation.
30. The privately supervised runtime creates no public listening service in embedded mode.
31. The local default uses one database per user installation.
32. Repository state is materialized as a mutable current index plus a version journal.
33. Artifact bytes are stored as database blobs and referenced by artifact identity.
34. Only `preparing_repository` and `validating` are recoverable after unexpected runtime interruption.
35. Validation consumes immutable persisted inputs through `ValidationRequest` and returns `ValidationReport`.
36. Validation never receives the live agent workspace or model and publication authority.

---

# 11. Initial vertical slice

The first implementation should prove the control flow without implementing the complete product.

## Inputs

- one local repository;
- one natural-language read-only task;
- one model adapter;
- one fixed context policy;
- token, turn, model-call, and tool-call budgets;
- read-only repository capabilities.

## Supported repository operations

- prepare repository;
- search;
- retrieve source;
- expand one graph relation;
- retrieve alternate representation.

## Supported runtime behavior

- Python SDK starts a private Go runtime child process;
- create one run;
- register or locate the repository in the shared embedded database;
- pin one repository version and workspace version;
- start repository worker;
- retrieve initial context;
- call model;
- execute read-only repository tools;
- admit tool results through context policy;
- record events with artifact references;
- reconcile token estimates with actual usage;
- stop with final answer or explicit failure.

## Outputs

- final answer;
- usage summary;
- context ledger;
- event stream;
- terminal stop reason.

## Explicitly excluded

- file writes;
- command execution;
- patch generation;
- validation execution;
- PR publication;
- arbitrary Python callbacks;
- learned policies;
- multi-agent execution;
- MCP integrations;
- network tools.

---

# 12. Resolved architecture decisions

## Runtime embedding

The Go runtime is a privately supervised child process owned by the Python SDK.

## State persistence and topology

Kiln uses one embedded Turso-compatible database per user installation. The database contains multiple workspaces, repositories, runs, repository indexes, event history, and artifact blobs. Access is logically isolated by scoped runtime sessions. Hosted deployments may place the same logical schema in separate databases by tenant or execution domain.

## State materialization

Repository intelligence uses a mutable current index plus a version journal. The current index serves active retrieval; the journal records repository versions, workspace versions, mutations, invalidations, and refreshes.

## Context policy boundary

Policies may propose retrieval. The runtime validates and performs repository operations. Policies receive structured candidates and propose context transitions.

## Repository refresh

Kiln combines mandatory synchronous invalidation, incremental refresh, versioned repository and workspace state, and full rebuild fallback. Users may configure refresh timing, but may not treat stale evidence as current.

## Token estimation

- repository engine estimates candidate cost;
- model gateway performs provider-specific final counting;
- budget manager reconciles estimates with actual usage.

## Event payload policy

The event store keeps first-class facts describing what happened. Large inputs, outputs, products, and payloads are stored as artifact blobs and referenced from events.

## Artifact storage

Artifacts are stored in the installation database as blobs. They remain immutable, content-hashed, and referenced by artifact identity. The subsystem supports compression, retention, garbage collection, export, and deletion.

## Runtime restart and recovery

Only `preparing_repository` and `validating` are recoverable after an unexpected runtime exit. Interruptions in other active states become terminal `runtime_interrupted` failures in the initial architecture.

## Validation ownership and integration

Validation is a separate package sharing Kiln's core contracts. The run coordinator invokes it out of process using an immutable `ValidationRequest` and receives a `ValidationReport`. Local deployments use a privately supervised validation worker; hosted deployments may use a remote isolated build service implementing the same contracts.

---

# 13. Remaining architecture questions

The previously identified architecture questions are resolved. Further open questions should be captured in the focused design documents where they arise rather than kept as product-level ambiguities here.

---

# 14. Near-term design deliverables

The next documents should be produced in this order:

1. `ARCHITECTURE.md`
   - this document;
   - component ownership;
   - lifecycle;
   - persistence;
   - invariants.

2. `docs/contracts.md`
   - semantic definitions of core domain objects;
   - required fields;
   - ownership;
   - lifecycle.

3. `docs/run-lifecycle.md`
   - legal state transitions;
   - transition preconditions;
   - failure paths;
   - emitted events.

4. `docs/repository-protocol.md`
   - scoped repository sessions;
   - repository operations;
   - request and response semantics;
   - candidate model;
   - version and refresh rules.

5. `docs/events.md`
   - event taxonomy;
   - causation and correlation;
   - replay requirements;
   - payload versus artifact rules.

6. `docs/persistence.md`
   - shared database domains;
   - scope and isolation;
   - repository and workspace versioning;
   - state, event, and artifact relationships.

7. `docs/security.md`
   - capability model;
   - trust boundaries;
   - child-process supervision;
   - worker isolation;
   - model egress;
   - default-deny behavior.

8. `docs/validation.md`
   - validation package boundary;
   - shared contracts;
   - clean-workspace requirements;
   - local and hosted integration.

9. `docs/vertical-slice.md`
   - first implementation scope;
   - end-to-end acceptance criteria;
   - excluded features.

---

# 15. First milestone

The first milestone is complete when Kiln can perform this workflow:

```text
Python developer submits a read-only repository question
    ↓
Python SDK privately starts the Go runtime
    ↓
Kiln creates a run and pins repository and workspace versions
    ↓
Python repository engine prepares searchable evidence
    ↓
Go runtime selects context under a fixed token budget
    ↓
Model requests repository evidence as needed
    ↓
Runtime validates and performs read-only requests
    ↓
Context policy decides what results enter later model calls
    ↓
Model gateway performs final token counting
    ↓
Budget manager reconciles actual usage
    ↓
Runtime records first-class events and artifact references
    ↓
Kiln returns a final answer and explicit usage summary
```

This milestone proves the main architectural boundaries:

- Python public interface;
- privately supervised Go runtime;
- Python repository engine;
- shared scoped persistence;
- version-bound structured evidence;
- budget-aware context;
- explicit capabilities;
- auditable events;
- artifact-referenced payloads.
