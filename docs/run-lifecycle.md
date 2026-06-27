# Kiln Run Lifecycle

## Status

Draft

## Purpose

This document defines the authoritative lifecycle for a Kiln run.

It specifies:

- lifecycle states;
- legal transitions;
- transition ownership;
- transition preconditions;
- state mutations;
- required events;
- failure behavior;
- cancellation behavior;
- recovery behavior;
- terminal outcomes.

This document does not define:

- concrete Go or Python types;
- database tables;
- transport encodings;
- provider-specific retry rules;
- implementation package layout.

Those artifacts must conform to the lifecycle semantics defined here.

---

### 1. Lifecycle principles

#### 1.1 The run coordinator owns lifecycle state

The run coordinator is the only component that may change a run's top-level lifecycle state.

Other components may return outcomes or request transitions, but they do not update lifecycle state directly.

Examples:

- the repository session manager reports that repository preparation succeeded;
- the agent loop proposes completion;
- the validation package reports that validation passed;
- the budget manager reports exhaustion;
- the process supervisor reports runtime interruption.

The run coordinator evaluates those outcomes and performs the corresponding legal transition.

#### 1.2 Every transition is explicit

A run never changes state implicitly because a component returned.

Each transition must have:

- a source state;
- a target state;
- a reason;
- a causal operation;
- a persisted state update;
- at least one lifecycle event.

#### 1.3 State changes and lifecycle events are atomic

The persisted state transition and its primary lifecycle event must be committed atomically.

The system must not expose:

- a new lifecycle state without its transition event;
- a transition event without the corresponding lifecycle state.

#### 1.4 Exactly one active top-level state

At any point, a run has exactly one top-level lifecycle state.

Sub-operations may have their own states, but they do not replace or overlap the run state.

For example, while a run is `running`, a model call may be `pending` and a repository request may later be `completed`. The run itself remains `running`.

#### 1.5 Terminal states are immutable

Once a run enters a terminal state, no further lifecycle transition is legal.

Post-run operations such as export, inspection, replay, or publication are separate workflows. They do not reopen the run.

#### 1.6 External effects do not define lifecycle state

The runtime must persist intent before starting an external or worker operation and persist the outcome after it completes.

A child process exit, model response, or validation result is an input to the state machine, not a state transition by itself.

#### 1.7 Recovery is state-specific

Only lifecycle states explicitly marked recoverable may resume after runtime interruption.

The initial architecture permits recovery from:

- `preparing_repository`;
- `validating`.

Interrupted runs in other non-terminal states transition to `failed`.

---

### 2. Lifecycle states

Kiln uses the following top-level states:

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

From any non-terminal state, a run may transition to one of these terminal states when the corresponding condition applies:

```text
failed
cancelled
exhausted
```

#### 2.1 State categories

##### Pre-execution states

- `created`
- `initializing`
- `preparing_repository`

##### Active execution states

- `running`
- `producing_output`

##### Post-execution state

- `validating`

##### Terminal states

- `completed`
- `failed`
- `cancelled`
- `exhausted`

---

### 3. Transition overview

| Source                 | Target                 | Trigger                                      |
| ---------------------- | ---------------------- | -------------------------------------------- |
| —                      | `created`              | Valid run specification accepted             |
| `created`              | `initializing`         | Coordinator begins runtime setup             |
| `initializing`         | `preparing_repository` | Runtime dependencies initialized             |
| `preparing_repository` | `running`              | Repository session is ready                  |
| `running`              | `producing_output`     | Completion proposal accepted                 |
| `producing_output`     | `validating`           | Output assembled and validation required     |
| `producing_output`     | `completed`            | Output assembled and validation not required |
| `validating`           | `completed`            | Validation passed and run result finalized   |
| any non-terminal       | `cancelled`            | Authorized cancellation accepted             |
| any non-terminal       | `exhausted`            | Hard budget or deadline exhausted            |
| any non-terminal       | `failed`               | Unrecoverable runtime or component failure   |

Transitions not listed above are illegal.

---

### 4. Common transition contract

Every lifecycle transition records the following semantic fields:

- run identity;
- source state;
- target state;
- transition reason;
- transition timestamp;
- causal operation identity;
- correlation identity, when part of a larger workflow;
- actor or component requesting the transition;
- resulting run-state version;
- related error, budget, validation, or artifact references.

#### 4.1 Transition ordering

Lifecycle transitions are totally ordered within a run.

Each successful transition advances a monotonic run-state version or sequence.

Concurrent components may propose outcomes, but the coordinator serializes transition decisions.

#### 4.2 Transition conflicts

When competing terminal conditions arrive concurrently, the coordinator resolves them using persisted ordering and the following precedence rules:

1. An already committed terminal transition wins.
2. A cancellation accepted before another terminal transition wins.
3. A hard budget exhaustion committed before successful completion wins.
4. A successful completion transition requires all completion preconditions to remain true at commit time.
5. Otherwise, the first valid transition committed wins.

No run may acquire multiple terminal reasons.

---

### 5. State specification

#### 5.1 `created`

##### Meaning

The run specification has been accepted and assigned a run identity, but runtime initialization has not begun.

##### Entered from

- run creation only.

##### Required persisted state

- run identity;
- immutable run specification;
- creation timestamp;
- installation or tenant scope;
- requested repository reference;
- requested budgets;
- requested security profile;
- requested model and context policy;
- validation requirement;
- lifecycle state `created`.

##### Entry preconditions

- the run specification is structurally valid;
- referenced configuration is resolvable;
- the caller is authorized to create the run;
- the run identity does not already exist.

##### Entry actions

- persist the run specification;
- initialize run-state version;
- create the first lifecycle event.

##### Required events

- `run.created`.

##### Permitted operations

- inspect run metadata;
- cancel;
- begin initialization.

##### Exit transitions

- `initializing`;
- `cancelled`;
- `failed`.

##### Failure examples

- persistence failure;
- invalid durable configuration reference;
- duplicate run identity.

---

#### 5.2 `initializing`

##### Meaning

The coordinator is establishing the trusted runtime dependencies required to execute the run.

##### Entered from

- `created`.

##### Entry preconditions

- the run specification is durably stored;
- no terminal transition has been committed.

##### Entry actions

The coordinator begins establishing:

- state and event storage;
- artifact storage access;
- budget state;
- capability grants;
- model adapter or gateway;
- context policy;
- repository adapter;
- deadlines;
- worker supervision;
- run-scoped security context.

##### Required persisted state

- initialized or pending budget ledger;
- effective capability grants;
- effective deadline;
- selected adapters;
- initialization operation identities.

##### Required events

- `run.initialization_started`;
- component-specific initialization events as applicable.

##### Completion condition

Initialization succeeds only when:

- budget limits are valid;
- required capability grants are established;
- required adapters are available;
- event and artifact persistence are writable;
- the runtime can begin repository preparation.

##### Exit transitions

- `preparing_repository`;
- `cancelled`;
- `exhausted`;
- `failed`.

##### Failure behavior

Initialization failures are not recoverable in the initial architecture.

Examples:

- unsupported model configuration;
- unavailable required adapter;
- invalid capability profile;
- database migration failure;
- artifact store unavailable.

##### Required completion event

- `run.initialization_completed`.

##### Required failure event

- `run.initialization_failed`.

---

#### 5.3 `preparing_repository`

##### Meaning

Kiln is resolving, pinning, indexing, and opening the repository state required by the run.

##### Entered from

- `initializing`;
- recovery of an interrupted `preparing_repository` state.

##### Entry preconditions

- initialization completed;
- repository read capability exists;
- repository reference is available;
- repository preparation budget can be reserved where applicable.

##### Preparation stages

Repository preparation is modeled as a series of idempotent stages:

1. resolve workspace;
2. resolve logical repository;
3. pin base repository version;
4. establish initial workspace version;
5. verify or materialize source snapshot;
6. inspect current-index compatibility;
7. load, refresh, or build the mutable current index;
8. synchronize required evidence;
9. start or reconnect the repository worker;
10. open a scoped repository session;
11. verify repository-session health.

Each stage records completion before the next stage begins.

##### Required persisted state

- workspace identity;
- repository identity;
- base repository-version identity;
- current workspace-version identity;
- source revision and content digest;
- preparation stage checkpoints;
- index status;
- repository-worker operation identity;
- repository-session identity when opened.

##### Required events

At minimum:

- `repository.preparation_started`;
- `repository.version_pinned`;
- `repository.index_preparation_started`;
- `repository.session_opened`;
- `repository.preparation_completed`.

Additional events may record:

- index reuse;
- incremental refresh;
- full rebuild;
- stale evidence invalidation;
- preparation retry;
- worker restart.

##### Completion condition

The run may enter `running` only when:

- repository identity is resolved;
- base repository version is pinned;
- current workspace version is established;
- the current index is compatible and synchronized for required operations;
- a scoped repository session is open;
- the repository worker is healthy;
- required read-only repository operations are available;
- no cancellation or exhaustion condition is pending.

##### Exit transitions

- `running`;
- `cancelled`;
- `exhausted`;
- `failed`.

##### Recovery

`preparing_repository` is recoverable.

After runtime restart, the coordinator:

1. loads the persisted preparation checkpoint;
2. verifies committed stage outputs;
3. discards or rolls back incomplete transactions;
4. restarts from the first incomplete or invalid stage;
5. reopens transient worker sessions;
6. emits recovery events.

Transient process identities are never assumed to survive restart.

##### Recovery events

- `run.recovery_started`;
- `repository.preparation_resumed`;
- `run.recovery_completed` or `run.recovery_failed`.

##### Failure examples

- repository no longer available;
- pinned content digest mismatch;
- index migration failure;
- repository worker repeatedly fails;
- scoped repository session cannot be opened.

---

#### 5.4 `running`

##### Meaning

The agent loop is active and may reason, retrieve evidence, invoke the model, and request authorized tools.

##### Entered from

- `preparing_repository`.

##### Entry preconditions

- repository preparation completed;
- repository session is healthy;
- model invocation capability is available;
- effective budgets have remaining capacity;
- initial task and context state exist;
- no stale evidence is active as current context.

##### Entry actions

- initialize or confirm turn state;
- create initial context-planning operation;
- begin the agent loop.

##### Required persisted state

- current turn;
- task state;
- context state;
- budget state;
- capability grants;
- repository session;
- base repository version;
- current workspace version;
- pending operation, if any;
- conversation or model-interaction references.

##### Required entry event

- `run.execution_started`.

##### Permitted operation cycles

###### Context planning

```text
create plan input
→ policy proposes retrieval and context actions
→ runtime validates plan
→ context manager applies approved actions
```

###### Repository retrieval

```text
reserve repository-query budget
→ validate repository session and versions
→ perform retrieval
→ validate candidates
→ expose candidates to policy
```

###### Model invocation

```text
render active context
→ authorize model egress
→ count and reserve tokens
→ invoke model
→ reconcile actual usage
→ normalize response
```

###### Tool execution

```text
validate tool call
→ authorize capability
→ reserve budget
→ perform operation
→ process result into candidates
```

###### Workspace mutation

When write capabilities exist in later milestones:

```text
authorize write
→ apply mutation
→ advance workspace version
→ invalidate affected evidence
→ refresh before stale evidence is reused
```

##### Turn semantics

A turn is a runtime-defined reasoning unit.

A turn begins when the runtime prepares a model request and ends when the resulting model response and all directly selected follow-up processing have been persisted.

The exact number of repository requests or internal context-policy operations per turn may vary.

##### Completion proposal

The model may propose completion, but this does not change lifecycle state.

The stop controller evaluates:

- whether the task has a usable final output;
- whether pending effects remain;
- whether current repository evidence is synchronized where required;
- whether output requirements are satisfied;
- whether validation inputs can be produced;
- whether a terminal budget or cancellation condition has occurred.

##### Exit transitions

- `producing_output`;
- `cancelled`;
- `exhausted`;
- `failed`.

##### Non-recoverability

`running` is not recoverable in the initial architecture.

After unexpected runtime termination:

- the run transitions to `failed`;
- the terminal reason is `runtime_interrupted`;
- unresolved reservations are released or reconciled during failure finalization;
- partial artifacts and events remain inspectable;
- no agent-loop continuation is attempted.

##### Failure examples

- model gateway fails beyond retry policy;
- repository session becomes irrecoverably invalid;
- event persistence fails;
- context invariants are violated;
- tool execution produces an indeterminate side effect;
- runtime process exits unexpectedly.

---

#### 5.5 `producing_output`

##### Meaning

The agent loop has stopped, and the runtime is assembling the immutable proposed result.

##### Entered from

- `running`.

##### Entry preconditions

- the stop controller accepts a completion proposal;
- no model or tool operation remains in flight;
- all committed budget usage is reconciled;
- required current evidence is synchronized;
- the task state contains a final output proposal.

##### Entry actions

The runtime assembles:

- final answer;
- usage summary;
- terminal context ledger;
- provenance summary;
- changed-file manifest where applicable;
- patch artifact where applicable;
- model and tool execution summary;
- validation request inputs where validation is required.

##### Required persisted state

- output-production operation identity;
- final answer artifact or inline reference;
- usage summary;
- provenance references;
- patch artifact, when applicable;
- changed-file manifest, when applicable;
- validation requirement and profile.

##### Required events

- `run.output_production_started`;
- artifact creation events;
- `run.output_production_completed`.

##### Validation branch

If validation is required, the runtime must persist all immutable validation inputs before entering `validating`.

These include:

- base repository version;
- source snapshot artifact or resolvable immutable source reference;
- patch artifact;
- changed-file manifest;
- validation profile;
- security profile;
- validation budgets.

##### Exit transitions

- `validating`, when validation is required;
- `completed`, when validation is not required;
- `cancelled`;
- `exhausted`;
- `failed`.

##### Non-recoverability

`producing_output` is not recoverable in the initial architecture.

An unexpected interruption transitions the run to `failed`.

The runtime may retain already committed output artifacts, but it does not infer that output production completed.

##### Failure examples

- patch generation fails;
- final artifact cannot be stored;
- provenance cannot be finalized;
- immutable validation request cannot be assembled.

---

#### 5.6 `validating`

##### Meaning

The separate validation package is evaluating the proposed output in a clean execution environment.

##### Entered from

- `producing_output`;
- recovery of an interrupted `validating` state.

##### Entry preconditions

- immutable validation request is persisted;
- referenced artifacts exist and hashes are verified;
- validation profile is trusted and resolved;
- validation budget can be reserved;
- no publication occurs before validation completes.

##### Validation request

The persisted request includes:

- validation identity;
- run identity;
- repository identity;
- base repository version;
- immutable source snapshot reference;
- patch artifact reference;
- changed-file manifest;
- validation profile;
- security profile;
- validation budgets;
- expected report contract.

##### Validation execution

The run coordinator:

1. starts a privately supervised local validator or submits to a hosted validation service;
2. provides access only to the referenced immutable inputs;
3. tracks validation status;
4. records validation command and policy events;
5. receives a structured validation report;
6. validates the report contract and artifact references;
7. finalizes the run.

The validator:

1. materializes a clean workspace;
2. verifies the base source;
3. applies the patch;
4. verifies changed files;
5. runs required checks;
6. stores detailed outputs as artifacts;
7. returns a structured report;
8. destroys temporary state.

##### Required persisted state

- validation identity;
- immutable validation request;
- validation attempt number;
- validation status;
- validator execution reference;
- budget reservation;
- validation report reference when complete.

##### Required events

At minimum:

- `validation.started`;
- `validation.attempt_started`;
- check and command summary events;
- `validation.report_received`;
- `validation.completed`.

##### Validation outcomes

###### Passed

Validation ran successfully and all required checks passed.

The run may enter `completed`.

###### Failed

Validation ran successfully, but the proposed output did not satisfy requirements.

The run enters `failed` with stop reason `validation_failed`.

###### Error

Validation could not produce a trustworthy result.

The coordinator applies configured retry policy. After retries are exhausted, the run enters `failed` with stop reason `validation_error`.

###### Exhausted

Validation exceeded a hard validation or run budget.

The run enters `exhausted`.

###### Cancelled

An authorized cancellation was accepted.

The run enters `cancelled`.

##### Recovery

`validating` is recoverable because its inputs are immutable.

After runtime restart, the coordinator:

1. loads the immutable validation request;
2. verifies input artifact hashes;
3. checks whether a valid completed report was already committed;
4. if so, finalizes from that report;
5. otherwise, marks any prior transient attempt interrupted;
6. starts a new validation attempt;
7. preserves prior attempt history.

Validation attempts are distinct, but the validation request identity remains stable.

##### Recovery events

- `run.recovery_started`;
- `validation.resumed`;
- `validation.attempt_restarted`;
- `run.recovery_completed` or `run.recovery_failed`.

##### Exit transitions

- `completed`;
- `cancelled`;
- `exhausted`;
- `failed`.

---

#### 5.7 `completed`

##### Meaning

The run finished successfully and has a finalized result.

##### Entered from

- `producing_output` when validation is not required;
- `validating` when validation passed.

##### Entry preconditions

- final answer or declared successful output exists;
- all required artifacts are committed;
- all budget usage is reconciled;
- no operation remains in flight;
- validation passed when required;
- exactly one successful stop reason is assigned.

##### Required persisted state

- terminal status `completed`;
- terminal stop reason;
- final result;
- final usage summary;
- event-stream bounds;
- artifact references;
- validation report when applicable;
- completion timestamp.

##### Required events

- `run.completed`.

##### Post-terminal behavior

The following may read the run without changing its lifecycle:

- inspection;
- export;
- replay;
- evaluation;
- publication workflow;
- artifact retention or garbage collection.

Publication is not part of the run lifecycle.

---

#### 5.8 `failed`

##### Meaning

The run ended because Kiln could not complete it successfully and the condition was not classified as cancellation or hard resource exhaustion.

##### Entered from

- any non-terminal state.

##### Entry preconditions

- an unrecoverable failure exists;
- configured retries or recovery are unavailable or exhausted;
- no prior terminal state is committed.

##### Failure classes

Examples include:

- invalid runtime state;
- repository preparation failure;
- model failure;
- tool failure;
- persistence failure;
- output-production failure;
- validation failure;
- validation infrastructure error;
- runtime interruption in a non-recoverable state;
- internal invariant violation.

##### Required persisted state

- terminal status `failed`;
- one terminal stop reason;
- normalized failure category;
- failure details or artifact reference;
- last successful lifecycle state;
- unresolved operation disposition;
- final usage summary where available;
- failure timestamp.

##### Required events

- component-specific failure event;
- `run.failed`.

##### Cleanup

Before committing failure, the coordinator attempts to:

- cancel in-flight workers;
- release or reconcile reservations;
- close repository sessions;
- persist useful partial artifacts;
- mark transient operations interrupted;
- remove temporary execution state.

Cleanup failure does not replace the original terminal reason, but it is recorded separately.

---

#### 5.9 `cancelled`

##### Meaning

An authorized actor requested cancellation and the coordinator accepted it before another terminal state was committed.

##### Entered from

- any non-terminal state.

##### Cancellation sources

- Python SDK caller;
- hosted workflow;
- operator;
- deadline controller, when modeled as cancellation rather than exhaustion;
- parent orchestration workflow.

##### Cancellation protocol

1. persist cancellation request;
2. verify authorization;
3. mark cancellation pending;
4. signal in-flight operations;
5. wait for bounded cooperative shutdown;
6. force termination where policy permits;
7. reconcile state and budgets;
8. commit terminal transition.

##### Required persisted state

- cancellation requester;
- cancellation reason;
- request timestamp;
- acceptance timestamp;
- interrupted operation identities;
- final usage summary where available.

##### Required events

- `run.cancellation_requested`;
- `run.cancellation_accepted`;
- operation cancellation events;
- `run.cancelled`.

##### Cancellation semantics

Cancellation is best effort until the terminal transition is committed.

An external operation may complete concurrently. The coordinator still applies terminal-transition conflict rules.

---

#### 5.10 `exhausted`

##### Meaning

The run ended because a hard budget, limit, or deadline prevented further progress.

##### Entered from

- any non-terminal state.

##### Exhaustion sources

- input-token budget;
- output-token budget;
- model-call limit;
- tool-call limit;
- repository-query limit;
- turn limit;
- cost limit;
- wall-clock deadline;
- command execution budget;
- validation budget;
- artifact-size limit when classified as hard exhaustion.

##### Entry preconditions

- the applicable budget manager reports a hard limit reached or an operation cannot be safely reserved;
- no prior terminal state is committed;
- configured degradation or fallback strategy cannot continue within limits.

##### Required persisted state

- exhausted budget domain;
- configured limit;
- committed usage;
- reserved usage disposition;
- operation that triggered exhaustion;
- partial result reference where available;
- final usage summary.

##### Required events

- budget-specific exhaustion event;
- `run.exhausted`.

##### Partial output

The run may preserve a partial answer or artifacts, but they are explicitly marked incomplete and do not change the terminal state.

---

### 6. Internal operation lifecycle

Top-level run state is supplemented by operation records.

An operation represents one bounded action such as:

- repository preparation stage;
- repository query;
- context plan;
- model invocation;
- tool invocation;
- workspace mutation;
- output generation;
- validation attempt.

#### 6.1 Operation states

```text
planned
  → authorized
  → reserved
  → started
  → completed
```

Alternative terminal states:

```text
denied
failed
cancelled
interrupted
exhausted
```

Not every operation requires every intermediate state, but effects and budgeted operations should record authorization and reservation where applicable.

#### 6.2 Operation invariants

- An operation belongs to exactly one run.
- An operation records its causal predecessor.
- An effectful operation cannot start before authorization.
- A budgeted operation cannot start before reservation.
- Completion records actual usage.
- Interrupted operations are never silently treated as completed.
- Retry creates a new attempt identity linked to the original operation.

---

### 7. Agent-loop lifecycle within `running`

The following sequence repeats while the run remains `running`.

#### 7.1 Prepare turn

Preconditions:

- no terminal condition;
- repository session healthy;
- required current evidence synchronized;
- sufficient budget remains to make progress.

Actions:

- increment or initialize turn identity;
- snapshot task and context state;
- emit `turn.started`.

#### 7.2 Plan context

Actions:

- construct policy input;
- allow retrieval proposals;
- validate proposed retrieval;
- perform approved repository requests;
- pass candidates back to the policy;
- validate context transitions;
- apply approved transitions.

Required events may include:

- `context.plan_requested`;
- `repository.query_started`;
- `repository.query_completed`;
- `context.plan_produced`;
- `context.item_admitted`;
- `context.item_evicted`;
- `context.plan_applied`.

#### 7.3 Invoke model

Actions:

- render provider-neutral messages;
- produce provenance map;
- authorize egress;
- perform provider-specific token count;
- reserve budget;
- store request artifact;
- invoke model;
- store response artifact;
- reconcile usage.

Required events may include:

- `model.request_rendered`;
- `model.egress_authorized`;
- `budget.reserved`;
- `model.invocation_started`;
- `model.invocation_completed`;
- `budget.committed`.

#### 7.4 Interpret response

The runtime normalizes the response into zero or more proposals:

- repository retrieval;
- tool call;
- workspace mutation;
- task-state update;
- completion.

The runtime rejects malformed or unsupported proposals without granting authority.

#### 7.5 Perform selected follow-up

Each approved proposal follows its own operation lifecycle.

Results become structured candidates or task-state updates. They do not enter model context directly.

#### 7.6 End turn

Actions:

- persist resulting task state;
- persist resulting context state;
- reconcile turn usage;
- evaluate stop conditions;
- emit `turn.completed`.

Possible outcomes:

- start another turn;
- enter `producing_output`;
- enter a terminal state.

---

### 8. Cancellation behavior by state

| State                  | Cancellation behavior                                                                  |
| ---------------------- | -------------------------------------------------------------------------------------- |
| `created`              | Cancel immediately after persisting request                                            |
| `initializing`         | Stop adapter setup and clean initialized resources                                     |
| `preparing_repository` | Cancel worker/index operations; preserve reusable committed index work                 |
| `running`              | Cancel model/tool/repository operations; do not resume                                 |
| `producing_output`     | Stop artifact assembly; preserve committed artifacts as partial                        |
| `validating`           | Cancel active validation attempt; preserve immutable request and prior attempt history |

Cancellation does not delete run history.

---

### 9. Exhaustion behavior by state

#### 9.1 Before execution

Exhaustion during `initializing` or `preparing_repository` produces no successful task output.

Reusable repository index work may remain committed if it is installation-level state rather than run-private state.

#### 9.2 During execution

Exhaustion during `running`:

- stops new operations;
- attempts to cancel in-flight operations;
- reconciles reservations;
- preserves partial task state and artifacts;
- emits an incomplete-result reference when useful.

#### 9.3 During output production

If output artifacts cannot be completed within remaining limits, the run becomes `exhausted`.

#### 9.4 During validation

Validation-budget exhaustion causes the overall run to become `exhausted`, not `failed`.

---

### 10. Retry semantics

Retries occur within a lifecycle state and do not themselves change top-level state.

#### 10.1 Retryable operations

Potentially retryable operations include:

- repository-worker startup;
- idempotent repository queries;
- model calls known not to have completed;
- artifact reads;
- validator startup;
- validation attempts;
- transient external-service requests.

#### 10.2 Non-retryable operations

Operations should not be retried automatically when completion is indeterminate and effects may have occurred.

Examples:

- arbitrary command with unknown side effects;
- workspace write without transactional confirmation;
- external integration write;
- publication action.

#### 10.3 Retry records

Each attempt records:

- parent operation identity;
- attempt number;
- retry reason;
- backoff or scheduling metadata;
- outcome.

Retries consume budget unless an explicit policy says otherwise.

---

### 11. Recovery after runtime restart

#### 11.1 Restart detection

When the Python SDK starts a new Go runtime against the installation database, the runtime scans for non-terminal runs whose owning runtime session is no longer active.

Each such run is classified by persisted lifecycle state.

#### 11.2 Recovery matrix

| Persisted state        | Initial behavior                                                 |
| ---------------------- | ---------------------------------------------------------------- |
| `created`              | Mark `failed` unless creation is still owned by active submitter |
| `initializing`         | Mark `failed`                                                    |
| `preparing_repository` | Resume from persisted preparation checkpoint                     |
| `running`              | Mark `failed` with `runtime_interrupted`                         |
| `producing_output`     | Mark `failed` with `runtime_interrupted`                         |
| `validating`           | Resume or restart validation from immutable request              |
| terminal state         | No recovery action                                               |

#### 11.3 Recovery ownership

Only one runtime process may claim recovery ownership for a run.

Recovery claim must be persisted atomically to prevent concurrent resumption.

#### 11.4 Recovery completion

A successful recovery returns the run to the same recoverable lifecycle state and continues its normal transitions.

Recovery does not create a new run identity.

---

### 12. Event requirements

#### 12.1 Lifecycle events

Required lifecycle event types:

- `run.created`;
- `run.initialization_started`;
- `run.initialization_completed`;
- `repository.preparation_started`;
- `repository.preparation_completed`;
- `run.execution_started`;
- `run.output_production_started`;
- `run.output_production_completed`;
- `validation.started`;
- `validation.completed`;
- `run.completed`;
- `run.failed`;
- `run.cancellation_requested`;
- `run.cancelled`;
- `run.exhausted`;
- `run.recovery_started`;
- `run.recovery_completed`;
- `run.recovery_failed`.

#### 12.2 Event facts versus artifacts

Lifecycle events store first-class facts:

- state transition;
- reason;
- operation identity;
- usage;
- status;
- referenced domain identities;
- artifact identities.

Large content remains in artifact blobs:

- prompts;
- model responses;
- patches;
- logs;
- validation details;
- source snapshots.

#### 12.3 Event ordering

Events have a monotonic sequence within a run.

Component-local timestamps assist diagnostics but do not replace run sequence ordering.

---

### 13. Terminal stop reasons

Terminal state and stop reason are separate concepts.

The state gives the broad outcome. The stop reason gives the specific cause.

#### 13.1 Successful stop reasons

Examples:

- `task_completed`;
- `answer_produced`;
- `validated_change_produced`.

#### 13.2 Failure stop reasons

Examples:

- `invalid_run_specification`;
- `initialization_failed`;
- `repository_preparation_failed`;
- `repository_session_failed`;
- `model_failed`;
- `tool_failed`;
- `persistence_failed`;
- `output_production_failed`;
- `validation_failed`;
- `validation_error`;
- `runtime_interrupted`;
- `internal_invariant_violation`.

#### 13.3 Cancellation stop reasons

Examples:

- `cancelled_by_user`;
- `cancelled_by_workflow`;
- `cancelled_by_operator`.

#### 13.4 Exhaustion stop reasons

Examples:

- `input_token_budget_exhausted`;
- `output_token_budget_exhausted`;
- `model_call_budget_exhausted`;
- `tool_call_budget_exhausted`;
- `repository_query_budget_exhausted`;
- `turn_budget_exhausted`;
- `cost_budget_exhausted`;
- `wall_time_exhausted`;
- `validation_budget_exhausted`.

Stop reasons should be a closed, versioned taxonomy with optional structured details.

---

### 14. Run result finalization

A terminal run produces a `RunResult`.

#### 14.1 Common fields

Every terminal result includes:

- run identity;
- terminal state;
- stop reason;
- started and ended timestamps;
- final usage summary;
- base repository version;
- final workspace version;
- event-stream bounds;
- artifact references;
- validation reference when applicable.

#### 14.2 Completed result

A completed result additionally includes:

- final answer or successful output;
- patch artifact when produced;
- validation report when required;
- provenance summary.

#### 14.3 Failed result

A failed result additionally includes:

- normalized failure category;
- failure details or artifact reference;
- last successful lifecycle state;
- partial output references where available.

#### 14.4 Cancelled result

A cancelled result additionally includes:

- cancellation requester;
- cancellation reason;
- interrupted operation identities.

#### 14.5 Exhausted result

An exhausted result additionally includes:

- exhausted budget domain;
- configured limit;
- final committed usage;
- partial output reference where available.

---

### 15. Lifecycle invariants

1. The run coordinator is the only owner of top-level lifecycle state.
2. A run has exactly one top-level state at a time.
3. Every lifecycle transition is explicit and persisted.
4. State transition and primary lifecycle event are committed atomically.
5. Lifecycle transitions are totally ordered within a run.
6. Only transitions listed in this document are legal.
7. Terminal states are immutable.
8. Every terminal run has exactly one stop reason.
9. No component result changes lifecycle state by itself.
10. External operations are recorded as planned before execution begins.
11. Effectful operations require capability authorization before start.
12. Budgeted operations require reservation before start.
13. Completion requires all in-flight operations to be resolved.
14. Completion requires usage reconciliation.
15. Validation inputs are immutable before entering `validating`.
16. Publication is outside the run lifecycle.
17. `preparing_repository` recovery resumes from persisted idempotent checkpoints.
18. `validating` recovery restarts or resumes from immutable inputs.
19. `running` is not recoverable in the initial architecture.
20. `producing_output` is not recoverable in the initial architecture.
21. Interrupted non-recoverable states terminate as `failed`.
22. Cancellation and exhaustion preserve event history and committed artifacts.
23. A failed validation produces `failed`, not `completed`.
24. Validation-budget exhaustion produces `exhausted`, not `failed`.
25. Partial output never changes an unsuccessful terminal state into success.
26. Stale repository evidence cannot be used as current evidence during any transition.
27. Only one runtime process may own or recover a non-terminal run.
28. Retry attempts are distinct operations and remain within the same top-level state.
29. Cleanup errors are recorded but do not overwrite the original terminal reason.
30. Final result construction occurs exactly once for a terminal run.

---

### 16. Initial vertical-slice lifecycle

The first vertical slice uses this reduced path:

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
completed
```

Validation is architecturally defined but not required in the first read-only milestone.

#### 16.1 Vertical-slice success path

1. Python SDK submits a valid read-only run specification.
2. Runtime creates the run.
3. Runtime initializes budgets, read-only capabilities, persistence, model gateway, and fixed context policy.
4. Runtime resolves and prepares the repository.
5. Runtime opens a scoped read-only repository session.
6. Agent loop performs context planning, repository retrieval, and model invocation.
7. Model proposes a final answer.
8. Stop controller accepts completion.
9. Runtime assembles the answer, usage summary, context ledger, and event references.
10. Run enters `completed`.

#### 16.2 Vertical-slice failure paths

The first implementation must support:

- invalid initialization;
- repository preparation failure;
- model failure;
- repository-worker failure;
- budget exhaustion;
- user cancellation;
- runtime interruption;
- persistence failure.

#### 16.3 Vertical-slice recovery

The first implementation recovers only interrupted repository preparation.

Validation recovery becomes required when validation is implemented.

---

### 17. Open lifecycle questions

The architecture-level lifecycle is complete enough for implementation planning. The following details remain for later protocol and implementation documents:

- exact retry limits and backoff policies;
- exact operation taxonomy;
- whether `created` runs may be reclaimed rather than failed after interruption;
- timeout behavior for forced cancellation;
- checkpoint granularity inside repository preparation;
- how hosted workflow ownership leases are represented;
- whether future milestones add recoverable agent-loop checkpoints;
- whether validation failure may optionally return to `running` for repair in a new run or workflow.

These questions do not alter the initial legal top-level state machine.
