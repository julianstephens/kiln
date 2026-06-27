# Kiln Validation

## Status

Draft

## Purpose

This document defines Kiln's validation subsystem.

Validation is responsible for independently evaluating a proposed repository change before it is considered safe for publication or downstream use.

Validation is a separate package that shares Kiln's core contracts but does not depend on the internal agent loop.

This document defines:

- validation ownership;
- validation request and report contracts;
- clean-workspace execution;
- validation profiles;
- check orchestration;
- security boundaries;
- local and hosted integration;
- persistence and events;
- retries, cancellation, recovery, and exhaustion;
- publication eligibility;
- initial milestone requirements.

It does not define:

- concrete implementation language;
- CI-provider-specific configuration;
- exact command syntax;
- repository-specific test suites;
- organization-specific approval policy.

---

## 1. Validation principles

### 1.1 Validation is independent

The component that generated a patch does not decide whether it is valid.

The agent may run tests during its work, but those results do not replace final validation.

### 1.2 Validation uses immutable inputs

Validation receives:

- an immutable base repository version;
- an immutable source snapshot or resolvable source reference;
- an immutable patch artifact;
- an immutable changed-file manifest;
- a trusted validation profile;
- a trusted security profile.

Validation never consumes the agent's live mutable workspace as authoritative input.

### 1.3 Validation runs in a clean environment

Validation materializes a fresh workspace from the base source and applies the proposed patch.

This avoids trusting:

- leftover generated files;
- mutated caches;
- untracked files;
- modified dependencies;
- process state from the agent runner.

### 1.4 Validation is policy-driven

The validation profile determines required checks.

The model cannot weaken or skip required checks.

### 1.5 Validation does not publish

Validation produces a report.

A separate publisher decides whether to create a branch, commit, or pull request.

### 1.6 Validation is recoverable

The `validating` lifecycle state is recoverable because its inputs are immutable.

A new attempt may be started after interruption without changing the validation request.

### 1.7 Validation fails closed

An incomplete, malformed, or unverifiable report is not treated as success.

---

## 2. Validation ownership

### 2.1 Runtime responsibilities

The Kiln runtime owns:

- deciding when validation begins;
- creating the validation request;
- verifying immutable inputs;
- reserving validation budgets;
- starting or submitting validation;
- tracking attempts;
- receiving and validating the report;
- persisting validation lifecycle state;
- deciding the run's terminal state;
- emitting authoritative validation events.

### 2.2 Validation package responsibilities

The validation package owns:

- constructing a clean workspace;
- materializing the base source;
- verifying source identity;
- applying the patch;
- checking the changed-file manifest;
- executing required checks;
- enforcing validation command restrictions;
- collecting bounded results;
- storing detailed outputs as artifacts;
- producing a structured report;
- cleaning up temporary state.

### 2.3 Publisher responsibilities

The publisher owns:

- verifying validation success;
- checking approval state;
- verifying patch identity;
- acquiring publication credentials;
- creating repository-side publication artifacts.

---

## 3. Validation boundary

Conceptually:

```text
Kiln runtime
    │
    │ ValidationRequest
    ▼
Validation package or service
    │
    │ ValidationReport
    ▼
Kiln runtime
```

The validation package may execute:

- as a private local child process;
- in a local container;
- in a hosted Fargate task;
- in CodeBuild;
- in another isolated build service.

The semantic contracts remain the same.

---

## 4. Validation identity model

### 4.1 Validation identity

Represents one immutable validation request associated with one run output.

### 4.2 Validation attempt identity

Represents one execution attempt of the validation request.

Retries create new attempt identities.

### 4.3 Check identity

Represents one check inside an attempt.

Examples:

- patch applicability;
- path policy;
- formatter;
- linter;
- type checker;
- test suite;
- secret scan;
- dependency policy.

### 4.4 Report identity

Represents one finalized structured report for a validation request.

At most one report is accepted as authoritative for finalization.

---

## 5. Validation request contract

A `ValidationRequest` contains immutable inputs.

### 5.1 Required fields

- validation identity;
- run identity;
- repository identity;
- base repository-version identity;
- base revision;
- base source snapshot artifact or immutable source reference;
- patch artifact reference;
- patch content hash;
- changed-file manifest;
- validation profile identity and version;
- security profile identity and version;
- validation budgets;
- creation timestamp;
- expected report-contract version.

### 5.2 Optional fields

- task identity;
- language or build metadata;
- repository-specific configuration reference;
- expected changed paths;
- expected test targets;
- approval policy;
- requested execution platform;
- cache policy.

### 5.3 Immutability

After the run enters `validating`, the request cannot change.

A changed patch or profile requires a new validation identity.

### 5.4 Request validation

Before submission, the runtime verifies:

- all referenced artifacts exist;
- hashes match;
- base revision is resolvable;
- validation profile is trusted;
- security profile is trusted;
- budgets are valid;
- patch and manifest refer to the same output.

---

## 6. Changed-file manifest

The changed-file manifest is a first-class validation input.

It contains:

- normalized repository-relative path;
- mutation type;
- prior content hash, when applicable;
- resulting content hash, when applicable;
- file mode changes;
- rename source and target, when applicable;
- expected patch membership.

The validator independently computes the actual changed-file set after applying the patch.

A mismatch is a validation failure.

---

## 7. Validation profile

A validation profile defines required checks and acceptance rules.

### 7.1 Profile ownership

Profiles come from trusted configuration.

They may be selected by:

- repository;
- organization;
- workflow;
- security class;
- task type.

### 7.2 Profile contents

A profile may include:

- patch applicability requirement;
- allowed changed paths;
- prohibited changed paths;
- maximum changed-file count;
- maximum patch size;
- formatter checks;
- lint checks;
- type checks;
- unit tests;
- integration tests;
- security scans;
- secret scans;
- dependency policy;
- generated-file policy;
- code-coverage thresholds;
- timeout and resource limits;
- network policy;
- approval rules.

### 7.3 Required and advisory checks

Checks may be:

- required;
- advisory;
- informational.

A required failed check blocks success.

An advisory failed check appears in the report but may not block publication eligibility.

### 7.4 Profile inheritance

Profiles may inherit from trusted parent profiles.

Effective profile resolution occurs before validation starts and is persisted with the request.

---

## 8. Security profile

The validation security profile controls execution authority.

It may define:

- filesystem roots;
- command allowlist;
- shell policy;
- environment policy;
- network policy;
- CPU limit;
- memory limit;
- process-count limit;
- output limit;
- artifact-write limit;
- credential access.

Validation profiles define what checks to run.

Security profiles define what the validator is allowed to do.

---

## 9. Clean workspace lifecycle

### 9.1 Create workspace

The validator creates a temporary isolated workspace.

### 9.2 Materialize base source

The validator materializes the exact base repository version.

It verifies:

- source revision;
- content digest;
- snapshot hash;
- repository identity.

### 9.3 Apply patch

The validator applies the immutable patch.

Patch application must be:

- deterministic;
- bounded;
- recorded;
- rejected on conflict.

### 9.4 Verify changed files

The validator compares actual changes against the manifest.

### 9.5 Run checks

Checks execute according to dependency and ordering rules.

### 9.6 Collect artifacts

Detailed output is stored as artifacts.

### 9.7 Produce report

A structured report is returned.

### 9.8 Destroy workspace

Temporary execution state is removed.

Cleanup failure is recorded but does not alter check results.

---

## 10. Check model

A validation check is one bounded evaluation.

### 10.1 Check fields

A check contains:

- check identity;
- check type;
- name;
- required/advisory classification;
- dependencies;
- execution specification;
- timeout;
- resource limits;
- expected outputs;
- acceptance rules.

### 10.2 Check statuses

- `pending`;
- `running`;
- `passed`;
- `failed`;
- `error`;
- `cancelled`;
- `exhausted`;
- `skipped`.

### 10.3 Check results

A result contains:

- status;
- start and end time;
- exit status, when applicable;
- bounded summary;
- diagnostics;
- artifact references;
- resource usage;
- failure reasons.

### 10.4 Skip semantics

A required check may be skipped only when the profile explicitly permits it.

Otherwise, inability to execute a required check is an error.

---

## 11. Check orchestration

### 11.1 Dependency graph

Checks may depend on earlier checks.

Example:

```text
patch applies
    ↓
path policy
    ↓
dependency install
    ↓
lint ─┬─ type check
      └─ unit tests
```

### 11.2 Parallelism

Independent checks may run concurrently if:

- security profile permits;
- budgets allow;
- result ordering remains deterministic;
- shared workspace effects are controlled.

### 11.3 Fail-fast

Profiles may choose:

- fail fast on first required failure;
- continue all checks;
- continue only advisory checks.

### 11.4 Ordering

The report preserves declared check order and actual execution order.

---

## 12. Built-in check families

### 12.1 Patch applicability

Verifies that the patch applies cleanly to the base source.

### 12.2 Changed-path policy

Verifies:

- only allowed paths changed;
- protected paths unchanged;
- rename policy;
- file count and patch-size limits.

### 12.3 Manifest consistency

Verifies actual changes match the supplied manifest.

### 12.4 Formatting

Runs trusted formatter checks.

### 12.5 Linting

Runs trusted lint checks.

### 12.6 Type checking

Runs language-specific type checks.

### 12.7 Tests

Runs approved test commands.

Possible scopes:

- affected tests;
- unit tests;
- integration tests;
- full suite.

### 12.8 Secret scanning

Scans patch and resulting workspace for secret material.

### 12.9 Dependency policy

Checks:

- dependency manifest changes;
- lock-file changes;
- approved registries;
- prohibited packages;
- version constraints.

### 12.10 Workflow and infrastructure policy

Checks changes to:

- CI workflows;
- deployment files;
- infrastructure code;
- production configuration.

### 12.11 Generated-file policy

Verifies whether generated files are expected and reproducible.

---

## 13. Command execution

Validation commands are structured.

A command specification contains:

- executable;
- arguments;
- working directory;
- environment additions;
- timeout;
- expected exit codes;
- output limits;
- network requirement;
- cache requirement.

Arbitrary shell strings are unavailable by default.

The validator must enforce the security profile independently of repository-provided scripts.

---

## 14. Repository-provided build configuration

Repository configuration may describe how to build or test, but it is untrusted input.

The validation profile decides whether repository-provided commands are allowed.

Examples:

- trusted fixed command from organization profile;
- repository script name selected from allowlist;
- generated command rejected;
- arbitrary project shell script denied.

---

## 15. Dependency installation

Dependency installation is high risk.

### 15.1 Default

Network access is denied.

### 15.2 Allowed installation

When required, installation may use:

- approved internal mirror;
- prebuilt cache;
- vendored dependencies;
- locked dependency set;
- controlled package proxy.

### 15.3 Constraints

The profile may require:

- lock-file consistency;
- checksum verification;
- approved registry;
- no install scripts;
- bounded download size;
- no credential exposure.

---

## 16. Network policy

Validation has no general network access by default.

Network-enabled checks require explicit destinations and limits.

The validator must defend against:

- redirects;
- DNS rebinding;
- metadata-service access;
- private-address SSRF;
- arbitrary package registry access.

---

## 17. Validation budget

Validation has its own budget domains.

Possible limits include:

- total wall time;
- per-check wall time;
- CPU time;
- memory;
- process count;
- output bytes;
- artifact bytes;
- network bytes;
- retry count.

The runtime reserves validation budget before starting validation.

The validator reports actual usage.

---

## 18. Validation report contract

A `ValidationReport` is the authoritative validation output.

### 18.1 Required fields

- report identity;
- validation identity;
- run identity;
- attempt identity;
- report-contract version;
- overall status;
- base repository version;
- patch hash;
- changed-file summary;
- check results;
- security results;
- total usage;
- started and ended timestamps;
- artifact references;
- publication eligibility;
- approval requirement;
- failure reasons.

### 18.2 Overall statuses

- `passed`;
- `failed`;
- `error`;
- `cancelled`;
- `exhausted`.

### 18.3 Status semantics

#### Passed

All required checks succeeded and report integrity is valid.

#### Failed

Validation completed, but one or more required acceptance rules failed.

#### Error

Validation could not produce a trustworthy acceptance result.

#### Cancelled

An authorized cancellation interrupted validation.

#### Exhausted

A hard validation budget was reached.

### 18.4 Publication eligibility

Publication eligibility is separate from overall status.

Examples:

- passed and eligible;
- passed but approval required;
- passed but protected path requires manual review;
- failed and ineligible.

### 18.5 Approval requirement

The report may include:

- no approval required;
- approval required;
- approval groups;
- approval reasons.

The validator does not grant approval.

---

## 19. Report verification

The runtime verifies:

- report schema version;
- validation identity;
- run identity;
- attempt identity;
- patch hash;
- base repository version;
- artifact hashes;
- required check presence;
- overall-status consistency;
- publication-eligibility consistency.

Malformed or inconsistent reports are treated as validation errors.

---

## 20. Validation attempts

### 20.1 Attempt lifecycle

```text
created
→ starting
→ running
→ reporting
→ completed
```

Alternative terminal outcomes:

- failed;
- error;
- cancelled;
- exhausted;
- interrupted.

### 20.2 Retry

Retries create new attempt identities.

The validation request remains unchanged.

### 20.3 Retryable conditions

Potentially retryable:

- worker startup failure;
- transient infrastructure failure;
- artifact-read failure;
- temporary build-service failure.

Not normally retryable:

- failed tests;
- protected-path violation;
- secret detection;
- patch conflict;
- deterministic lint failure.

---

## 21. Cancellation

The runtime may cancel active validation.

The validator:

- stops launching new checks;
- signals active commands;
- waits for bounded shutdown;
- force-terminates where permitted;
- stores partial results;
- returns cancelled status.

Cancellation does not mutate immutable inputs.

---

## 22. Recovery

### 22.1 Recoverable state

The top-level run state `validating` is recoverable.

### 22.2 Recovery sequence

After runtime restart:

1. load validation request;
2. verify input artifacts and hashes;
3. inspect prior attempts;
4. accept a previously committed valid report if present;
5. otherwise mark interrupted attempt;
6. create a new attempt;
7. rerun validation.

### 22.3 Recovery ownership

Only one runtime may claim recovery.

### 22.4 Determinism

Repeated validation may produce different timing or nondeterministic test output.

The report preserves attempt history.

---

## 23. Local integration

Locally, the runtime starts a privately supervised validation process.

```text
Python SDK
    └── Go runtime
          └── validation worker
```

### 23.1 Transport

Use:

- private pipe;
- socket pair;
- Unix domain socket;
- Windows named pipe.

### 23.2 Persistence access

The validator receives a scoped persistence session allowing access only to:

- its validation request;
- referenced source snapshot;
- patch artifact;
- changed-file manifest;
- its own output artifacts.

It does not receive a general installation database handle.

### 23.3 Process environment

The validator receives:

- minimal environment;
- no model credentials;
- no publication credentials;
- no unrelated host secrets.

---

## 24. Hosted integration

Hosted validation may execute in:

- CodeBuild;
- Fargate;
- Kubernetes job;
- internal build service.

### 24.1 Request transport

The workflow passes:

- validation request identity;
- immutable artifact references;
- scoped execution identity;
- callback or result destination.

### 24.2 Result transport

The validator stores artifacts and returns a structured report.

### 24.3 Semantic consistency

Local and hosted validators implement the same request and report contracts.

---

## 25. Persistence

The validation domain stores:

- validation requests;
- validation attempts;
- check states;
- reports;
- artifact references;
- budget usage;
- recovery state.

### 25.1 Atomic request creation

Commit together:

- immutable request;
- validated artifact references;
- lifecycle transition to `validating`;
- validation-request event.

### 25.2 Report commit

Commit together:

- report record;
- check summaries;
- artifact references;
- validation-completed event;
- resulting run transition when final.

---

## 26. Events

Required events include:

- `validation.request_created`;
- `validation.started`;
- `validation.attempt_started`;
- `validation.workspace_materialized`;
- `validation.patch_applied`;
- `validation.check_started`;
- `validation.check_completed`;
- `validation.check_failed`;
- `validation.report_received`;
- `validation.completed`;
- `validation.failed`;
- `validation.error`;
- `validation.cancelled`;
- `validation.exhausted`;
- `validation.resumed`.

Large outputs remain artifact-backed.

---

## 27. Security

### 27.1 No publication authority

The validator cannot publish.

### 27.2 No model authority

The validator cannot invoke the agent model unless an explicit validation check requires a separately approved model capability.

The default profile grants none.

### 27.3 Scoped source access

The validator sees only the base source and proposed patch.

### 27.4 Clean execution

Validation runs in a fresh environment.

### 27.5 Command restrictions

Only profile-approved commands execute.

### 27.6 Secrets

Secrets are not injected unless a check explicitly requires a narrowly scoped secret.

### 27.7 Artifact output

Output is scanned and bounded before persistence.

---

## 28. Publication handoff

A successful validation does not itself publish.

The publisher receives:

- run identity;
- validation report;
- validated patch artifact;
- patch hash;
- base revision;
- approval state;
- publication metadata.

The publisher verifies:

- validation passed;
- report integrity;
- patch hash match;
- required approvals;
- repository scope.

---

## 29. Validation outcome and run lifecycle

### 29.1 Passed

```text
validating
    ↓
completed
```

### 29.2 Failed checks

```text
validating
    ↓
failed
reason: validation_failed
```

### 29.3 Validation infrastructure error

Retry according to policy.

After retry exhaustion:

```text
validating
    ↓
failed
reason: validation_error
```

### 29.4 Exhaustion

```text
validating
    ↓
exhausted
reason: validation_budget_exhausted
```

### 29.5 Cancellation

```text
validating
    ↓
cancelled
```

---

## 30. Initial validation milestone

Validation is not required for the first read-only repository-question milestone.

The first change-producing milestone should support:

- one immutable base snapshot;
- one patch artifact;
- one changed-file manifest;
- one trusted validation profile;
- clean patch application;
- protected-path check;
- one formatter or linter;
- one test command;
- bounded command output;
- validation report;
- recovery from interrupted validation;
- no network;
- no publication.

---

## 31. Validation invariants

1. Validation is independent of the agent loop.
2. Validation consumes immutable inputs.
3. Validation never trusts the live agent workspace as final input.
4. Validation runs in a clean environment.
5. Validation profiles are trusted configuration.
6. Model output cannot weaken validation requirements.
7. Security profiles independently constrain validator execution.
8. Required checks must be present in the report.
9. Required failed checks block success.
10. A malformed report is not success.
11. Patch hash and base revision must match the request.
12. Changed-file manifest is independently verified.
13. Validation cannot publish.
14. Validation receives no publication credentials.
15. Validation receives no model credentials by default.
16. Validation has no network by default.
17. Commands are structured and allowlisted.
18. Validation output is bounded and artifact-backed.
19. Retries create new attempt identities.
20. The validation request remains unchanged across retries.
21. `validating` is recoverable from immutable inputs.
22. Only one report is accepted as authoritative.
23. Publication eligibility is distinct from validation status.
24. Approval is distinct from validation.
25. Validation-budget exhaustion produces run exhaustion.
26. Failed checks produce `validation_failed`.
27. Infrastructure failure produces `validation_error`.
28. Cleanup failure is recorded separately.
29. Local and hosted validators share the same contracts.
30. Publisher verifies the validated patch hash.

---

## 32. Open validation questions

The validation boundary is complete enough for implementation planning. Remaining details include:

- exact validation profile format;
- exact check taxonomy;
- command sandbox implementation;
- cache strategy;
- dependency installation policy;
- default fail-fast behavior;
- test-target selection;
- code-coverage support;
- flaky-test handling;
- hosted result callback protocol;
- approval integration;
- report-signing or attestation;
- exact cleanup guarantees;
- maximum report size;
- whether model-assisted validation is ever supported.

These questions do not change the core validation semantics.
