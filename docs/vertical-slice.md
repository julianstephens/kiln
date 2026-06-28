# Kiln Initial Vertical Slice

## Status

Draft

## Purpose

This document defines Kiln's first end-to-end implementation milestone.

The vertical slice is intentionally narrow. Its purpose is to prove the core architectural boundaries with the smallest complete workflow that produces useful behavior.

The first milestone answers one read-only question about one local repository.

It exercises:

- the Python developer interface;
- the privately supervised Go runtime;
- the Python repository worker;
- shared installation persistence;
- scoped repository sessions;
- structured repository evidence;
- context planning;
- budget enforcement;
- remote or local model invocation;
- model egress controls;
- event and artifact persistence;
- explicit terminal outcomes.

It does not attempt to prove code mutation, command execution, validation, publication, learned policies, or multi-agent orchestration.

---

## 1. Milestone statement

The milestone is complete when a Python developer can submit a natural-language question about a local repository and receive a grounded answer while Kiln:

1. privately starts the Go runtime;
2. resolves and prepares the repository;
3. opens a version-bound repository session;
4. retrieves structured repository evidence;
5. selects evidence under explicit budgets;
6. invokes one approved model;
7. performs additional read-only retrieval as requested;
8. records the complete execution history;
9. returns an answer, usage summary, context ledger, and stop reason.

Example task:

> Find the repository indexing entry point, inspect its implementation, identify its direct callers, and explain the indexing flow.

---

## 2. Product boundary exercised

The vertical slice proves this boundary:

```text
Python application
        │
        ▼
Python SDK
        │ private protocol
        ▼
Go runtime
   ├── run coordinator
   ├── agent loop
   ├── context manager
   ├── fixed context policy
   ├── budget manager
   ├── capability broker
   ├── model gateway
   ├── event/state/artifact persistence
   └── repository client
            │ private protocol
            ▼
      Python repository worker
```

The developer does not need to write or call Go directly.

---

## 3. User experience

The target developer experience is conceptually:

```python
from kiln import Agent, Budget
from kiln.models import Model

agent = Agent.open(
    repository=".",
    model=Model(...),
    budget=Budget(
        max_input_tokens=32_000,
        max_output_tokens=4_000,
        max_model_calls=8,
        max_repository_queries=24,
        max_turns=12,
    ),
)

result = agent.run(
    "Find the repository indexing entry point, inspect its implementation, "
    "identify its direct callers, and explain the indexing flow."
)

print(result.answer)
print(result.usage)
print(result.stop_reason)
```

The exact API is deferred to implementation design. The required semantics are not.

### 3.1 Required inputs

- local repository path;
- natural-language task;
- approved model configuration;
- fixed context policy configuration;
- explicit budgets;
- read-only security profile.

### 3.2 Required outputs

- final answer;
- terminal status;
- stop reason;
- usage summary;
- context ledger;
- event-stream reference;
- artifact references;
- repository and workspace version identities.

---

## 4. Scope

### 4.1 Included

The first milestone includes:

- one user installation database;
- one local repository per run;
- one task per run;
- one agent loop;
- one model adapter;
- one fixed-cap context policy;
- repository preparation;
- lexical or full-text search;
- source retrieval;
- one graph expansion relation;
- one alternate source representation;
- read-only capabilities;
- input-token budget;
- output-token budget;
- model-call budget;
- repository-query budget;
- turn budget;
- wall-time budget;
- event persistence;
- database-backed artifact storage;
- cancellation;
- explicit failures;
- recovery during repository preparation;
- replay-oriented provenance.

### 4.2 Explicitly excluded

The first milestone excludes:

- file writes;
- workspace mutation;
- patch generation;
- command execution;
- test execution;
- validation execution;
- PR publication;
- GitHub credentials;
- arbitrary network tools;
- MCP integrations;
- third-party Python policies;
- third-party Python tools;
- custom Python model callbacks;
- learned retrieval gates;
- learned compression;
- embeddings as a requirement;
- multi-agent execution;
- repository refresh during active execution;
- recovery of the running agent loop;
- hosted AWS orchestration;
- hostile multi-tenant isolation.

---

## 5. Assumptions

The first milestone assumes:

- the repository is locally available;
- the repository remains unchanged during a read-only run;
- the repository language is supported by the selected parser set;
- one approved model is reachable;
- the installation database is writable;
- the repository can be indexed within configured limits;
- no validation or publication is required.

External repository mutation during the run may cause the run to fail with a version-conflict or repository-changed reason.

---

## 6. Components required

### 6.1 Python SDK

Responsibilities:

- accept developer configuration;
- validate obvious local inputs;
- locate the Go runtime binary;
- start the runtime as a private child process;
- establish the runtime protocol;
- submit a run;
- stream events;
- receive the final result;
- close the runtime cleanly.

It does not:

- access the repository index directly;
- call the model directly;
- select context;
- authorize repository operations.

### 6.2 Runtime process supervisor

Responsibilities:

- own the Go child-process lifecycle;
- use a private channel;
- detect runtime exit;
- propagate cancellation;
- prevent public access;
- tie the runtime to the SDK session.

### 6.3 Run coordinator

Responsibilities:

- create the run;
- initialize dependencies;
- move through legal lifecycle states;
- open and close the repository session;
- start the agent loop;
- finalize the result;
- assign one terminal stop reason.

### 6.4 Agent loop

Responsibilities:

- coordinate context planning;
- invoke the model;
- interpret retrieval and completion proposals;
- perform approved repository requests;
- update task state;
- evaluate continuation.

### 6.5 Fixed context policy

Responsibilities:

- preserve pinned task and system context;
- propose initial retrieval;
- rank or order candidates using supplied scores;
- admit candidates up to a fixed token cap;
- reject candidates that do not fit;
- evict low-priority non-pinned items when necessary.

The policy is deterministic and built into the Go runtime.

It may propose retrieval, but the runtime performs it.

### 6.6 Context manager

Responsibilities:

- track available, active, observed, and evicted items;
- validate repository and workspace versions;
- apply approved plans;
- ensure stale evidence is not active;
- produce a context ledger.

### 6.7 Context renderer

Responsibilities:

- render provider-neutral messages;
- preserve trusted and untrusted content boundaries;
- produce provenance mapping;
- produce an estimated token count;
- store the rendered request as an artifact.

### 6.8 Budget manager

Responsibilities:

- initialize budgets;
- reserve before operations;
- commit actual usage;
- reconcile token estimates;
- deny unaffordable operations;
- emit exhaustion.

### 6.9 Capability broker

Responsibilities:

- grant read-only repository operations;
- grant one approved model invocation capability;
- deny writes, commands, publication, integrations, and general network access;
- record checks and denials.

### 6.10 Model gateway

Responsibilities:

- accept provider-neutral requests;
- perform provider-specific token counting;
- invoke one approved model;
- normalize responses;
- report actual usage;
- store request and response artifacts.

### 6.11 Model egress controller

Responsibilities:

- inspect rendered content;
- enforce provider and model allowlists;
- exclude protected paths;
- scan for obvious secret material;
- allow or deny the call;
- record the decision.

### 6.12 Repository session manager

Responsibilities:

- bind the run to one repository version and workspace version;
- validate session ownership;
- open, monitor, and close the repository session;
- reject version conflicts.

### 6.13 Repository worker

Responsibilities:

- register the repository;
- prepare or reuse the current index;
- parse supported files;
- extract files and symbols;
- build one relation family;
- support scoped retrieval operations;
- return structured candidates;
- estimate candidate tokens;
- persist preparation checkpoints.

### 6.14 Persistence layer

Responsibilities:

- one database per installation;
- persist installation metadata;
- persist workspaces and repositories;
- maintain current index and version journal;
- persist run state;
- append events;
- store artifact blobs;
- support recovery scan.

---

## 7. Required contracts

The first slice requires these domain contracts:

- `RunSpecification`;
- `RunState`;
- `Workspace`;
- `Repository`;
- `RepositoryVersion`;
- `WorkspaceVersion`;
- `RepositorySession`;
- `RepositoryCandidate`;
- `ContextItem`;
- `ContextPlan`;
- `ModelRequest`;
- `ModelResponse`;
- `BudgetState`;
- `CapabilityGrant`;
- `Operation`;
- `Event`;
- `ArtifactReference`;
- `RunResult`.

Validation-specific contracts may exist in documentation but are not exercised.

---

## 8. Required protocols

### 8.1 Runtime protocol

Minimum operations:

- `runtime.health`;
- `run.create`;
- `run.cancel`;
- `run.status`;
- `run.events`;
- `run.result`;
- `runtime.close`.

### 8.2 Repository protocol

Minimum operations:

- `repository.register`;
- `repository.prepare`;
- `repository.status`;
- `repository.open`;
- `repository.search`;
- `repository.get_source`;
- `repository.expand_graph`;
- `repository.get_representation`;
- `repository.close`;
- worker health;
- worker shutdown.

### 8.3 Model adapter boundary

Minimum operations:

- capabilities;
- token counting;
- completion;
- cancellation.

A custom callback protocol is not required.

---

## 9. Repository intelligence scope

### 9.1 File discovery

The worker must:

- walk the repository;
- honor configured ignore rules;
- normalize repository-relative paths;
- reject path escape;
- identify supported files;
- record file hashes.

### 9.2 Symbol extraction

The worker must extract enough structure to support:

- symbol-name search;
- qualified names;
- source ranges;
- source retrieval.

### 9.3 Search

The milestone requires one deterministic lexical or full-text search implementation.

Semantic embeddings are optional and not required for acceptance.

### 9.4 Graph relation

The milestone requires one graph relation, preferably direct callers or calls.

The chosen relation must support:

- bounded traversal;
- confidence or derivation metadata;
- exact source identities.

### 9.5 Representations

The milestone requires:

- full source;
- one lower-cost representation.

Recommended lower-cost representation:

- symbol signature; or
- file/symbol outline.

Generated summaries are not required.

---

## 10. Security profile

The first milestone uses a fixed read-only profile.

```text
repository:
    read: selected repository
    write: deny

filesystem:
    outside repository: deny

process:
    execute: deny

network:
    general: deny
    model provider: allow approved endpoint only

model:
    approved provider/model only
    excluded paths:
        - .env
        - **/*.pem
        - secrets/**
        - .git/**

extensions:
    deny

publication:
    deny
```

### 10.1 Security acceptance

The runtime must demonstrate:

- no public listener;
- no repository write capability;
- no process-execution capability;
- no publication capability;
- repository session scoping;
- egress evaluation before every remote call;
- security events for decisions.

---

## 11. Budgets

The first milestone supports these limits.

### 11.1 Model input tokens

Limits total model input across the run or per call according to configuration.

### 11.2 Model output tokens

Reserves output capacity for every call.

### 11.3 Model calls

Limits inference attempts.

### 11.4 Repository queries

Limits search, source, graph, and representation requests.

### 11.5 Turns

Limits agent-loop turns.

### 11.6 Wall time

Limits total run duration.

### 11.7 Budget behavior

For every budgeted operation:

```text
estimate
→ reserve
→ execute
→ commit actual usage
→ release unused reservation
```

An unaffordable operation is denied before execution.

---

## 12. Canonical success flow

```text
1. Developer opens Agent with local repository
        ↓
2. Python SDK starts private Go runtime
        ↓
3. SDK submits RunSpecification
        ↓
4. Runtime persists run.created
        ↓
5. Runtime initializes budgets, capabilities, model, policy
        ↓
6. Runtime registers/resolves repository
        ↓
7. Repository worker prepares or reuses index
        ↓
8. Runtime pins repository and workspace versions
        ↓
9. Runtime opens scoped repository session
        ↓
10. Agent loop starts first turn
        ↓
11. Policy proposes initial search
        ↓
12. Runtime reserves query budget and performs search
        ↓
13. Worker returns structured candidates
        ↓
14. Policy admits candidates under token cap
        ↓
15. Renderer creates model request and provenance map
        ↓
16. Egress controller evaluates request
        ↓
17. Gateway counts tokens and budget is reserved
        ↓
18. Model returns answer or repository-tool proposal
        ↓
19. Runtime performs approved read-only retrieval as needed
        ↓
20. Loop repeats until completion proposal is accepted
        ↓
21. Runtime produces final answer and context ledger
        ↓
22. Run enters completed
        ↓
23. SDK returns RunResult
```

---

## 13. Agent interaction model

The model may propose only:

- repository search;
- source retrieval;
- graph expansion;
- alternate representation retrieval;
- completion.

Unsupported proposals are rejected.

The model cannot propose:

- file writes;
- shell commands;
- network calls;
- publication;
- capability changes;
- security-profile changes.

### 13.1 Retrieval tool definitions

The model-visible repository tools should be narrow.

Conceptually:

```text
search_repository(query, limit, optional_path_scope)
get_source(content_id or path, optional_symbol)
expand_graph(content_ids, relation, depth, limit)
get_representation(content_id, representation)
```

The exact schema is deferred, but arbitrary database queries are prohibited.

---

## 14. Context-policy behavior

The fixed-cap policy should support:

### 14.1 Pinned content

Always preserve:

- system instructions;
- task;
- security constraints;
- essential task-state summary.

### 14.2 Candidate admission

Candidates are considered using:

- retrieval rank;
- semantic kind;
- graph distance;
- representation cost;
- duplicate status;
- prior observation.

### 14.3 Duplicate handling

The policy should avoid admitting duplicate identical content.

### 14.4 Capacity

The policy must preserve room for:

- fixed instructions;
- current task state;
- model output reservation;
- tool definitions.

### 14.5 Eviction

When active context exceeds its cap, the policy may evict non-pinned low-priority items.

### 14.6 No compression requirement

Learned or generated compression is deferred.

Representation replacement may use repository-provided lower-cost representations.

---

## 15. Persistence scope

### 15.1 Installation state

Persist:

- installation identity;
- schema version;
- runtime sessions.

### 15.2 Repository state

Persist:

- workspace;
- repository;
- repository version;
- workspace version;
- index generation;
- files;
- symbols;
- selected graph relation;
- source representations;
- preparation checkpoints;
- version journal.

### 15.3 Run state

Persist:

- immutable run specification;
- lifecycle state;
- task state;
- context items;
- budget state;
- capability grants;
- operations;
- final result.

### 15.4 Events

Persist all required milestone events.

### 15.5 Artifacts

Store as database blobs:

- rendered model requests;
- model responses;
- large candidate batches;
- provenance maps;
- final answer;
- final result;
- error details.

---

## 16. Required events

At minimum, the milestone emits:

### Runtime and lifecycle

- `runtime.session_started`;
- `runtime.session_ready`;
- `run.created`;
- `run.initialization_started`;
- `run.initialization_completed`;
- `run.execution_started`;
- `run.output_production_started`;
- `run.output_production_completed`;
- exactly one terminal run event.

### Repository

- `repository.preparation_started`;
- `repository.version_pinned`;
- `repository.preparation_completed`;
- `repository.worker_started`;
- `repository.session_opened`;
- query started and completed/failed;
- `repository.session_closed`.

### Context and policy

- `context.plan_requested`;
- `context.plan_produced`;
- `context.plan_applied`;
- candidate availability;
- context admission;
- context eviction where applicable;
- `context.rendered`.

### Model

- `model.request_rendered`;
- `model.egress_evaluated`;
- `model.invocation_started`;
- model completed/failed;
- `model.response_interpreted`.

### Budget

- `budget.initialized`;
- reservation;
- commit;
- reconciliation;
- denial or exhaustion when applicable.

### Turn

- `turn.started`;
- turn completed/failed.

### Artifacts

- artifact creation for model payloads;
- artifact creation for final result.

---

## 17. Run-result contract

A successful result includes:

- run identity;
- status `completed`;
- successful stop reason;
- final answer;
- repository identity;
- base repository version;
- final workspace version;
- usage summary;
- context ledger;
- event-stream bounds;
- artifact references;
- replay-completeness classification.

An unsuccessful result includes:

- terminal status;
- stop reason;
- failure or exhaustion details;
- partial answer when available;
- usage summary;
- event and artifact references.

---

## 18. Failure scenarios

The milestone must handle these failure classes.

### 18.1 Invalid run configuration

Examples:

- invalid repository path;
- unsupported model;
- impossible budget.

Expected result:

- `failed`;
- structured initialization reason.

### 18.2 Repository preparation failure

Examples:

- unreadable repository;
- unsupported database state;
- parser worker crash beyond retry policy.

Expected result:

- `failed`;
- repository preparation reason;
- preserved checkpoints where safe.

### 18.3 Model failure

Examples:

- provider unavailable;
- malformed response;
- repeated timeout.

Expected result:

- retry according to policy;
- then `failed`.

### 18.4 Budget exhaustion

Expected result:

- `exhausted`;
- exact budget domain;
- partial output where available.

### 18.5 Cancellation

Expected result:

- `cancelled`;
- in-flight operation cancellation;
- persisted partial history.

### 18.6 Runtime interruption

During `preparing_repository`:

- recovery is attempted.

During `running` or `producing_output`:

- run becomes `failed`;
- reason `runtime_interrupted`.

### 18.7 Repository version conflict

If the repository changes during execution:

- session becomes stale or conflict is detected;
- the run fails in the first milestone;
- no silent refresh occurs.

---

## 19. Recovery scope

### 19.1 Supported

The milestone supports recovery from interrupted `preparing_repository`.

Recovery uses:

- preparation checkpoints;
- current-index state;
- version journal;
- worker restart.

### 19.2 Unsupported

The milestone does not resume:

- active turns;
- model calls;
- output production.

These runs fail explicitly.

---

## 20. Acceptance criteria

The milestone is accepted when all mandatory criteria pass.

### 20.1 Developer interface

- A Python caller can create and execute one run.
- No Go API knowledge is required.
- Cancellation can be requested.
- Final result and streamed events are accessible.

### 20.2 Runtime process

- The Go runtime is privately supervised.
- No public TCP listener is created.
- Unexpected runtime exit is detected.
- Runtime close terminates child resources.

### 20.3 Repository preparation

- A local repository can be registered.
- A repository version and workspace version are pinned.
- The current index can be created and reused.
- Preparation checkpoints are persisted.
- Interrupted preparation can resume.

### 20.4 Repository protocol

- All retrieval uses a scoped session.
- Cross-session or wrong-version requests are rejected.
- Search, source, one graph relation, and one alternate representation work.
- Candidates carry version, provenance, cost, and completeness metadata.

### 20.5 Context

- Retrieved candidates do not enter context directly.
- The policy produces a plan.
- The runtime validates and applies the plan.
- Active context remains within the configured cap.
- The final context ledger is available.

### 20.6 Model

- One approved adapter works.
- Provider-specific preflight token counting occurs.
- Remote egress is evaluated.
- Model request and response artifacts are stored.
- Actual usage is reconciled.

### 20.7 Budgets

- Model-call, query, turn, input, output, and wall-time limits are enforced.
- Operations are denied before exceeding hard limits.
- Exhaustion produces an explicit terminal result.

### 20.8 Security

- Repository access is read-only.
- No command execution is available.
- No arbitrary network access is available.
- No publication authority is available.
- Excluded-path content is not sent to the remote model.
- Capability decisions are recorded.

### 20.9 Events and artifacts

- Required events are ordered and immutable.
- Large payloads are artifact-backed.
- The event stream identifies what the model saw.
- Terminal status has exactly one stop reason.

### 20.10 Persistence

- Runs survive process inspection after completion.
- Multiple repositories can share the installation database without query leakage.
- Artifact integrity can be verified.
- Database migrations have a version.

---

## 21. Required test scenarios

### 21.1 Happy path

Repository contains an identifiable indexing entry point and callers.

Expected:

- grounded answer;
- relevant source retrieved;
- graph relation used;
- completed state.

### 21.2 Index reuse

Run the same repository twice without changes.

Expected:

- second run reuses compatible current index;
- distinct runs and event streams;
- same repository version.

### 21.3 Repository isolation

Register two repositories with similar symbol names.

Expected:

- each scoped session returns only its repository's candidates.

### 21.4 Token-cap pressure

Use a small context cap with oversized candidates.

Expected:

- lower-cost representation or rejection;
- cap is not exceeded;
- decisions recorded.

### 21.5 Query-budget exhaustion

Set repository-query limit below task needs.

Expected:

- no extra query executes;
- terminal state `exhausted`;
- budget domain recorded.

### 21.6 Model-call exhaustion

Set model-call limit to one when more work is requested.

Expected:

- second call denied;
- explicit exhaustion.

### 21.7 Egress exclusion

Place matching content in an excluded path.

Expected:

- content is not included in remote request;
- egress event records exclusion.

### 21.8 Cancellation

Cancel during repository query or model call.

Expected:

- operation cancellation attempted;
- run terminal state `cancelled`;
- partial history preserved.

### 21.9 Worker crash during preparation

Terminate repository worker after a checkpoint.

Expected:

- worker restarts;
- preparation resumes from valid checkpoint;
- no partial index exposed.

### 21.10 Runtime crash during running

Terminate Go runtime during an active turn.

Expected:

- a later runtime detects the interrupted run;
- run becomes `failed`;
- stop reason `runtime_interrupted`.

### 21.11 Repository changes during run

Modify a source file externally after session open.

Expected:

- conflict detected before mismatched evidence is treated as current;
- run fails explicitly.

### 21.12 Artifact integrity

Corrupt a stored artifact in a test fixture.

Expected:

- hash verification fails;
- content is not silently consumed;
- structured error event emitted.

---

## 22. Demonstration scenario

A milestone demonstration should use a repository with:

- a clear indexing entry point;
- multiple direct callers;
- enough unrelated code to require search;
- one supported language;
- deterministic source.

Task:

> Find the repository indexing entry point, inspect its implementation, identify its direct callers, and explain the indexing flow. Cite the files and symbols used.

Expected answer qualities:

- identifies the correct entry point;
- explains its main stages;
- identifies direct callers;
- distinguishes evidence from inference;
- references exact repository paths or symbol identities;
- does not claim unsupported behavior.

Expected trace qualities:

- initial search;
- source retrieval;
- graph expansion;
- context admission decisions;
- one or more model invocations;
- explicit token and query usage;
- completed terminal event.

---

## 23. Milestone deliverables

### 23.1 Runtime

- private child-process executable;
- run coordinator;
- lifecycle state machine;
- agent loop;
- fixed context policy;
- context manager;
- budget manager;
- capability broker;
- model gateway;
- event/state/artifact persistence.

### 23.2 Python SDK

- runtime supervision;
- run submission;
- event streaming;
- cancellation;
- result retrieval.

### 23.3 Repository engine

- registration;
- preparation;
- current index;
- version journal;
- scoped sessions;
- search;
- source;
- one graph relation;
- one alternate representation.

### 23.4 Documentation

- architecture;
- contracts;
- run lifecycle;
- repository protocol;
- events;
- persistence;
- security;
- validation;
- this vertical-slice specification.

### 23.5 Tests

- contract tests;
- protocol tests;
- lifecycle tests;
- security tests;
- persistence tests;
- end-to-end test;
- recovery test.

---

## 24. Suggested implementation sequence

The vertical slice should be built in this order.

### Phase 1: Persistence foundation

- installation database;
- schema versioning;
- workspace/repository records;
- run records;
- event append;
- artifact blobs.

### Phase 2: Runtime protocol and supervision

- private process startup;
- health handshake;
- run submission;
- event streaming;
- close and cancellation.

### Phase 3: Repository preparation

- repository worker process;
- register;
- prepare;
- current index;
- checkpoints;
- session open.

### Phase 4: Retrieval

- search;
- source retrieval;
- one graph relation;
- candidate contract;
- alternate representation.

### Phase 5: Runtime control plane

- lifecycle transitions;
- operations;
- budgets;
- read-only capabilities;
- task and context state.

### Phase 6: Model loop

- context policy;
- renderer;
- egress;
- token count;
- model adapter;
- response interpretation.

### Phase 7: Finalization

- stop controller;
- output production;
- result contract;
- context ledger;
- session shutdown.

### Phase 8: Hardening

- cancellation;
- recovery;
- artifact integrity;
- version conflict;
- test scenarios;
- replay inspection.

---

## 25. Definition of done

The first vertical slice is done when:

1. the happy-path demonstration succeeds end to end;
2. all mandatory acceptance criteria pass;
3. all required failure scenarios produce explicit terminal outcomes;
4. repository isolation is demonstrated;
5. token and operation budgets are enforced;
6. no write, process, publication, or general-network authority exists;
7. the event stream reconstructs the model-visible context;
8. repository preparation recovers from interruption;
9. runtime interruption during execution fails safely;
10. the public workflow is Python-native.

---

## 26. Deferred next slices

After the first milestone, recommended slices are:

### Slice 2: Workspace mutation

Adds:

- file read/write tools;
- workspace versions;
- invalidation;
- incremental refresh;
- patch generation.

### Slice 3: Command sandbox

Adds:

- structured commands;
- test execution;
- output processing;
- command budgets.

### Slice 4: Validation

Adds:

- validation request;
- clean workspace;
- required checks;
- validation report;
- recovery.

### Slice 5: Hosted task-to-PR workflow

Adds:

- task ingress;
- repository broker;
- ephemeral runner;
- clean validation service;
- publisher;
- PR result.

### Slice 6: Policy experimentation

Adds:

- Python policy workers;
- learned retrieval;
- compression;
- evaluation and policy replay.

---

## 27. Vertical-slice invariants

1. The public interface is Python-native.
2. The Go runtime runs as a private child process.
3. Embedded mode creates no public listener.
4. One run operates on one pinned local repository state.
5. Repository access is read-only.
6. All repository operations use a scoped session.
7. Repository evidence is structured and version-bound.
8. Retrieval does not imply context admission.
9. The fixed policy proposes plans; the runtime applies them.
10. The context cap is enforced before model invocation.
11. Every model call receives egress authorization.
12. Every budgeted operation is reserved before execution.
13. Actual token usage is reconciled.
14. Model output is a proposal.
15. Unsupported effects are structurally unavailable.
16. Events are immutable and ordered.
17. Large content is stored as artifact blobs.
18. The final result has exactly one terminal state and stop reason.
19. Repository preparation is recoverable.
20. Active execution is not recoverable in the first milestone.
21. Multiple repositories may share the database without scope leakage.
22. External repository mutation is detected rather than silently accepted.
23. No validation or publication authority is present.
24. Success requires a grounded final answer and complete audit trace.
