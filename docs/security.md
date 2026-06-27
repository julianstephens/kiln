# Kiln Security

## Status

Draft

## Purpose

This document defines Kiln's security model.

Kiln is designed to execute repository-scale AI workflows while minimizing ambient authority, data leakage, cross-scope access, and unintended side effects.

This document defines:

- trust boundaries;
- security principles;
- capability semantics;
- process isolation;
- repository and filesystem access;
- command execution;
- network access;
- model egress;
- credential handling;
- prompt-injection defenses;
- worker and extension security;
- persistence security;
- validation and publication boundaries;
- local and hosted deployment requirements;
- auditing, recovery, and incident handling;
- initial vertical-slice requirements.

It does not define:

- platform-specific sandbox implementation;
- cloud-provider-specific IAM policy documents;
- cryptographic library choices;
- operating-system hardening commands;
- regulatory compliance mappings.

---

## 1. Security goals

Kiln should:

1. deny authority by default;
2. make all effects explicit and scoped;
3. treat model output as untrusted proposals;
4. treat repository content and tool output as untrusted evidence;
5. isolate risky components from the authoritative runtime;
6. prevent cross-run and cross-repository access;
7. prevent credentials from entering the agent runner unnecessarily;
8. control data sent to remote model providers;
9. preserve an auditable record of security-relevant decisions;
10. separate generation, validation, and publication authority.

---

## 2. Non-goals

Kiln does not claim to:

- make arbitrary imported Python packages safe in-process;
- provide perfect sandboxing on every operating system;
- prevent a fully compromised host administrator from reading local state;
- guarantee that remote model providers never retain submitted data;
- make prompt injection impossible through prompting alone;
- turn logical database scoping into adversarial tenant isolation;
- permit arbitrary shell access safely by default.

---

## 3. Security principles

### 3.1 Default deny

Capabilities not explicitly granted are unavailable.

Absence of a denial rule is not permission.

### 3.2 Least authority

Each component receives only the authority required for its role.

Examples:

- repository worker can inspect scoped repository data but cannot publish;
- validator can read immutable validation inputs but cannot invoke the model;
- publisher can publish validated artifacts but cannot execute generated code;
- model gateway can invoke an approved provider but cannot read arbitrary files.

### 3.3 Separation of proposal and execution

The model proposes.

The runtime validates.

The capability broker authorizes.

A controlled adapter or worker executes.

### 3.4 No ambient credentials

Credentials are not inherited broadly through environment variables or global configuration.

Credential use is explicit and mediated.

### 3.5 Narrow, typed operations

Effects use structured requests.

Kiln does not expose generic:

- shell strings;
- SQL endpoints;
- filesystem handles;
- arbitrary HTTP clients;
- dynamic tool-discovery trust.

### 3.6 Security decisions are observable

Capability grants, checks, denials, egress decisions, sensitive artifact access, and publication actions are recorded.

### 3.7 Embedded does not mean single process

The Python API owns the lifecycle, but the Go runtime and risky workers execute in private child processes.

### 3.8 Validation is independent

The component that generates a change does not decide whether it is safe to publish.

---

## 4. Trust classification

### 4.1 Trusted components

Trusted components include:

- Go runtime kernel;
- run coordinator;
- capability broker;
- budget manager;
- state-transition logic;
- event-store logic;
- built-in security policy evaluator.

A defect in these components may compromise Kiln's security guarantees.

### 4.2 Semi-trusted components

Semi-trusted components include:

- first-party repository engine;
- first-party model adapters;
- built-in tools;
- validation adapters;
- artifact codecs.

Their inputs and outputs are validated by the runtime.

### 4.3 Untrusted inputs and components

Untrusted elements include:

- repository contents;
- task-supplied content;
- model output;
- generated code;
- tool output;
- command output;
- external HTTP responses;
- issue and pull-request text;
- third-party Python extensions;
- custom tools;
- custom policies;
- custom model workers;
- build scripts;
- test suites.

Untrusted data may affect reasoning but does not grant authority.

---

## 5. Primary trust boundaries

Kiln has these major trust boundaries:

```text
Developer / external workflow
        │
        ▼
Python SDK
        │ private protocol
        ▼
Go runtime security kernel
   ├── model gateway boundary
   ├── repository worker boundary
   ├── tool worker boundary
   ├── command sandbox boundary
   ├── validation boundary
   └── persistence boundary
```

Hosted deployments add:

- ingress boundary;
- tenant boundary;
- cloud control-plane boundary;
- publication boundary;
- external provider boundary.

---

## 6. Capability model

### 6.1 Capability definition

A capability is an explicit, runtime-recognized grant of authority.

A capability includes:

- capability identity;
- capability type;
- scope;
- target;
- allowed operations;
- constraints;
- source of authority;
- expiration;
- revocation state.

### 6.2 Capability categories

Core categories include:

- repository read;
- repository write;
- artifact read;
- artifact write;
- process execute;
- network connect;
- model invoke;
- external integration read;
- external integration write;
- validation execute;
- publication execute;
- credential use.

### 6.3 Non-transitivity

Capabilities do not imply one another.

```text
repository.write ≠ process.execute
process.execute ≠ network.connect
model.invoke ≠ arbitrary HTTP
artifact.read ≠ repository.read
repository.read ≠ git.push
validation.execute ≠ publication.execute
```

### 6.4 Scope

Capability scope may include:

- installation;
- run;
- repository;
- repository version;
- workspace version;
- path patterns;
- executable identities;
- network destinations;
- provider/model pairs;
- artifact identities;
- operation classes.

### 6.5 Lifetime

Capabilities may be:

- run-scoped;
- operation-scoped;
- time-limited;
- single-use;
- revocable.

### 6.6 Authority source

A capability records where authority came from.

Examples:

- developer configuration;
- organization policy;
- hosted workflow;
- approved elevation;
- validation profile.

Model output is never an authority source.

### 6.7 Capability decision

Every effectful operation is checked by the capability broker before execution.

The decision is one of:

- allow;
- allow with narrower scope;
- deny;
- require approval.

### 6.8 Capability invariants

1. No effect occurs without a capability decision.
2. Grants are denied by default.
3. Grants are scoped and non-transitive.
4. Workers cannot mint grants.
5. Models cannot mint grants.
6. Tool registration does not imply permission to execute.
7. Capability use is auditable.
8. Revoked or expired grants are unusable.

---

## 7. Security profiles

A security profile is trusted configuration that declares effective authority for a run.

It may define:

- repository read scope;
- repository write scope;
- allowed executables;
- network policy;
- approved model providers;
- excluded paths;
- artifact retention;
- validation requirements;
- approval rules.

Example conceptual profile:

```text
SecurityProfile
├── repository
│   ├── read: all source
│   ├── write: src/**, tests/**
│   └── deny: .git/**, .env, **/*.pem
├── process
│   ├── shell: false
│   ├── executables: pytest, ruff
│   └── network: false
├── model
│   ├── providers: approved provider
│   ├── excluded paths: secrets/**
│   └── maximum egress bytes
└── publication
    └── unavailable to agent runner
```

Security profiles are not supplied or weakened by the model.

---

## 8. Runtime process security

### 8.1 Private supervision

The Python SDK starts the Go runtime as a privately supervised child process.

### 8.2 Communication

Communication uses:

- inherited pipes;
- private socket pairs;
- Unix domain sockets;
- Windows named pipes.

The runtime does not expose a public listening port in embedded mode.

### 8.3 Session ownership

The runtime channel is bound to one owning SDK session.

Unrelated local processes must not be able to submit requests.

### 8.4 Runtime environment

The runtime should receive a controlled environment.

Avoid inheriting unrelated secrets.

### 8.5 Runtime crash behavior

On unexpected exit:

- transient sessions become invalid;
- recoverable states may resume;
- non-recoverable active runs fail;
- security-relevant partial operations are reconciled.

---

## 9. Worker isolation

Risky or extensible components run outside the authoritative runtime process.

Examples:

- repository engine;
- custom Python policy;
- custom Python tool;
- local model worker;
- command runner;
- validator.

### 9.1 Worker authority

Workers receive:

- one operation request;
- narrow data access;
- narrow capabilities;
- bounded resources.

Workers do not receive the full runtime state or raw database access.

### 9.2 Worker protocol

Worker protocols are:

- typed;
- versioned;
- closed to unknown operations;
- bounded;
- correlated;
- cancellable.

### 9.3 Worker output

Worker output is untrusted and validated.

### 9.4 Worker discovery

Kiln does not dynamically trust arbitrary discovered workers.

Extensions must be explicitly registered by the host.

---

## 10. MCP posture

Kiln does not use MCP as its internal trust model.

The internal architecture does not permit:

- arbitrary server discovery;
- automatic trust in advertised tools;
- ambient credential forwarding;
- dynamic authority based on tool descriptions.

MCP may later be supported as an optional untrusted adapter behind the capability broker.

An MCP adapter would:

- expose only explicitly approved operations;
- receive no ambient credentials;
- run out of process;
- have bounded network and filesystem access;
- return untrusted results;
- remain unable to grant new capabilities.

---

## 11. Repository access security

### 11.1 Scoped repository sessions

Repository access occurs through a session bound to:

- one run;
- one repository;
- one repository version;
- one workspace version;
- one allowed operation set.

### 11.2 No generic SQL

The repository worker exposes typed operations, not generic SQL.

### 11.3 Path scope

All paths are normalized and repository-relative.

### 11.4 Escape prevention

The repository layer must defend against:

- `..`;
- symlink escape;
- junction escape;
- case-insensitive path confusion;
- alternate path separators;
- race conditions;
- hard-link surprises where relevant.

### 11.5 Repository metadata

Access to `.git` and repository metadata is separately scoped.

Reading source does not imply permission to alter Git state.

### 11.6 Revision binding

All evidence is bound to repository and workspace versions.

Stale evidence cannot be treated as current.

---

## 12. Filesystem security

### 12.1 Root separation

Execution should conceptually separate:

```text
/repository   controlled source view
/scratch      writable temporary space
/artifacts    controlled output area
/runtime      inaccessible to workers
/secrets      inaccessible to workers
```

### 12.2 Read operations

Read capabilities specify:

- allowed roots;
- allowed patterns;
- denied patterns;
- maximum bytes;
- content classes.

### 12.3 Write operations

Write capabilities specify:

- allowed paths;
- denied paths;
- operation types;
- maximum bytes;
- whether create/delete/rename are permitted.

### 12.4 Protected paths

Protected paths commonly include:

- `.git/**`;
- `.env`;
- secret files;
- signing keys;
- CI workflow files;
- production infrastructure;
- dependency lock files, depending on policy.

### 12.5 Time-of-check/time-of-use

The filesystem adapter should validate scope at operation time, not only during request parsing.

---

## 13. Command execution security

### 13.1 Structured commands

Commands are represented as:

- executable identity;
- argument list;
- working directory;
- environment additions;
- timeout;
- resource limits.

Arbitrary shell expressions are unavailable by default.

### 13.2 Executable allowlist

The security profile lists allowed executables and optionally allowed subcommands or argument patterns.

### 13.3 Environment

Command workers start with a minimal environment.

Secrets are not inherited.

### 13.4 Resource limits

Command execution should support:

- wall-clock timeout;
- CPU limit;
- memory limit;
- process-count limit;
- output-size limit;
- file-write limit;
- network policy.

### 13.5 Network

Command execution has no network access unless separately granted.

### 13.6 Effect uncertainty

If a command fails or is interrupted, the runtime records whether side effects are:

- none;
- known;
- partial;
- indeterminate.

Indeterminate effects block unsafe automatic retry.

---

## 14. Network security

### 14.1 Default

Network access is denied by default.

### 14.2 Destination scope

A network capability specifies:

- protocol;
- hostname or service identity;
- port;
- request method classes;
- optional path scope;
- maximum requests;
- maximum bytes;
- expiration.

### 14.3 DNS and redirects

Adapters should defend against:

- DNS rebinding;
- redirects to unapproved destinations;
- private-address SSRF;
- metadata-service access;
- alternate IP encodings.

### 14.4 Network mediation

Workers should not receive arbitrary sockets when a runtime-mediated client can enforce policy more safely.

---

## 15. Model invocation security

### 15.1 Model access is a capability

Model invocation is not ordinary network access.

A model capability specifies:

- provider;
- model;
- endpoint;
- maximum tokens;
- maximum bytes;
- allowed data classes;
- local or remote mode.

### 15.2 Egress controller

Every remote model call passes through the model egress controller.

### 15.3 Egress inputs

The controller evaluates:

- rendered request;
- content identities;
- source paths;
- provider;
- endpoint;
- security profile;
- exclusion rules;
- secret-scan results;
- byte and token limits.

### 15.4 Egress outcomes

- allow;
- redact;
- deny;
- require approval.

### 15.5 Egress audit

The runtime records:

- provider and model;
- content identities;
- excluded or redacted content;
- estimated and actual size;
- policy decision;
- artifact references.

### 15.6 Local models

Local models may avoid remote data egress, but their worker process remains untrusted and isolated.

---

## 16. Secret handling

### 16.1 No inherited secret environment

Workers do not inherit the host's full environment.

### 16.2 Secret references

Credentials are represented by references, not embedded values.

### 16.3 Credential broker

A credential broker resolves secrets only for authorized operations.

### 16.4 Direct versus mediated use

Prefer runtime-mediated API requests where possible.

When a worker must use a secret directly:

- grant is operation-scoped;
- value is injected temporarily;
- environment and logs are controlled;
- artifact and event output is scanned;
- secret is revoked or discarded after use.

### 16.5 Persistence

Secrets must not be persisted in:

- run specifications;
- events;
- artifacts;
- tool results;
- model messages;
- repository metadata.

---

## 17. Prompt injection model

Prompt injection is treated as an authorization problem, not merely a prompting problem.

### 17.1 Untrusted instruction sources

Potential instruction-bearing content includes:

- source comments;
- README files;
- tests;
- issue text;
- tool output;
- command output;
- web content;
- generated files.

### 17.2 Evidence labeling

Rendered context distinguishes:

- trusted system instructions;
- task instructions;
- repository evidence;
- tool output;
- model-authored content;
- external content.

### 17.3 Authority separation

Untrusted content cannot:

- register tools;
- grant capabilities;
- change security profile;
- alter model provider policy;
- authorize publication;
- access credentials.

### 17.4 Runtime enforcement

Even if the model follows malicious repository instructions, unauthorized operations remain structurally unavailable.

---

## 18. Tool security

### 18.1 Tool definition

A tool definition contains:

- tool identity;
- version;
- argument schema;
- result schema;
- required capability types;
- worker identity;
- risk classification.

### 18.2 Tool registration

Tools are explicitly registered by trusted host configuration.

### 18.3 Tool availability versus authority

A tool may be visible but unavailable if the current run lacks the required capability.

Prefer not exposing unavailable high-risk tools to the model.

### 18.4 Result handling

Tool results are untrusted candidates.

They pass through result processing and context policy before model admission.

### 18.5 Third-party tools

Third-party tools run out of process with:

- restricted filesystem;
- restricted network;
- no ambient secrets;
- bounded resources;
- typed protocol.

---

## 19. Policy security

### 19.1 Built-in policies

Built-in deterministic policies may run inside the trusted runtime.

### 19.2 Third-party policies

Third-party or experimental Python policies run in isolated workers.

### 19.3 Policy inputs

Policies receive immutable structured views, not raw runtime handles.

### 19.4 Policy outputs

Policies return declarative plans.

They cannot:

- execute retrieval directly;
- mutate context directly;
- spend budget directly;
- grant capabilities;
- access credentials.

### 19.5 Plan validation

The runtime validates every plan.

---

## 20. Persistence security

### 20.1 Installation database permissions

The local database should be accessible only to the owning user or service identity.

### 20.2 Logical scope

Every data object has explicit scope.

### 20.3 Raw database access

Workers and plugins do not receive general database handles.

They receive scoped persistence APIs or artifact references.

### 20.4 Artifact access

Artifact reads require scope and purpose checks.

### 20.5 Database blobs

Database-backed artifacts increase the impact of database compromise.

Retention, redaction, and local file permissions are therefore critical.

### 20.6 Encryption

Local encryption may rely initially on OS-level disk protection.

Hosted deployments require managed encryption and key controls.

### 20.7 Multi-tenancy

One shared database file is not sufficient for hostile tenant isolation.

Hosted deployments should separate databases or execution domains by tenant or security boundary.

---

## 21. Event and audit security

Security-relevant events include:

- capability grant;
- capability denial;
- egress decision;
- artifact access;
- secret detection;
- worker startup;
- worker failure;
- validation result;
- publication authorization;
- recovery claim.

Audit records must be:

- immutable;
- ordered;
- scoped;
- retention-controlled.

Raw sensitive content remains artifact-backed and access-controlled.

---

## 22. Validation security

### 22.1 Separate process

Validation runs outside the agent runtime.

### 22.2 Immutable inputs

Validation receives:

- immutable base source;
- immutable patch;
- trusted validation profile;
- trusted security profile.

### 22.3 No model authority

The validator does not receive model credentials or context.

### 22.4 Clean workspace

Validation materializes a clean workspace rather than reusing the agent's live environment.

### 22.5 Command restrictions

Validation commands are controlled by the validation profile.

### 22.6 Network

Validation has no network by default.

Dependency access, when required, must be explicitly mediated.

### 22.7 Output

Validation returns a structured report and artifact references.

It does not publish.

---

## 23. Publication security

Publication is outside the agent runtime.

### 23.1 Credential isolation

The agent runner never receives publication credentials.

### 23.2 Required inputs

Publisher accepts:

- validated patch;
- validation report;
- approval state;
- repository identity;
- base revision;
- publication metadata.

### 23.3 Short-lived credentials

Use short-lived, repository-scoped credentials.

### 23.4 Protected operations

Publisher may:

- create branch;
- create commit;
- open pull request.

It should not receive unnecessary administrative permissions.

### 23.5 Validation binding

The publisher verifies that the patch hash matches the validated artifact.

---

## 24. Local deployment security

The local embedded product should:

- start no public server;
- create no public TCP listener;
- use private child-process channels;
- use one user-owned installation database;
- inherit no unnecessary environment secrets;
- deny commands and network by default;
- use scoped repository sessions;
- record security decisions;
- provide explicit capability configuration.

Local security depends on the integrity of the host user account and operating system.

---

## 25. Hosted deployment security

Hosted deployments add:

- authenticated ingress;
- tenant isolation;
- ephemeral runners;
- private networking;
- separate validation;
- separate publisher;
- cloud audit controls.

### 25.1 Control plane versus execution plane

The control plane owns:

- task authorization;
- repository broker;
- orchestration;
- publisher.

The execution plane owns:

- ephemeral Kiln runner;
- scoped model access;
- temporary workspace;
- task artifacts.

### 25.2 Repository credentials

A trusted broker fetches the repository snapshot.

The runner receives no GitHub credential.

### 25.3 Model credentials

Prefer workload identity or a model proxy.

### 25.4 Network

Runners have no general internet access.

### 25.5 Account separation

High-assurance deployments may place execution in a separate cloud account or project.

---

## 26. Security failure behavior

Security failures should fail closed.

Examples:

- unknown capability;
- version mismatch;
- path escape;
- egress policy failure;
- secret detection;
- worker protocol mismatch;
- artifact-scope mismatch;
- publication hash mismatch.

A security failure produces:

- structured denial or failure;
- security event;
- no unauthorized effect.

---

## 27. Recovery security

### 27.1 Recovery ownership

Only one runtime may claim a recoverable run.

### 27.2 Lease validation

Recovery requires a persisted ownership lease.

### 27.3 Transient grants

Transient grants do not automatically survive restart.

They must be re-established from trusted configuration.

### 27.4 Recoverable states

Repository preparation and validation may resume because their checkpoints and inputs are durable and bounded.

### 27.5 Non-recoverable states

Active agent execution does not resume automatically in the initial architecture.

This avoids reusing uncertain capabilities, model calls, or effects.

---

## 28. Security events

Required security event types include:

- `capability.granted`;
- `capability.narrowed`;
- `capability.checked`;
- `capability.denied`;
- `capability.revoked`;
- `model.egress_evaluated`;
- `artifact.accessed`;
- `security.secret_detected`;
- `security.path_escape_rejected`;
- `security.protocol_violation`;
- `security.scope_mismatch`;
- `security.approval_required`;
- `security.approval_recorded`;
- `publication.authorized`;
- `publication.failed`.

---

## 29. Initial vertical-slice security

The first read-only milestone requires:

- private Python-SDK-to-Go-runtime channel;
- no public listener;
- read-only repository capability;
- scoped repository session;
- no workspace writes;
- no command execution;
- no arbitrary network tools;
- one approved model adapter;
- model egress decision for every remote call;
- secret and excluded-path checks before remote model calls;
- scoped installation database access;
- immutable security events;
- no publication credentials;
- no MCP integrations;
- no third-party callbacks.

### 29.1 Initial security profile

Conceptually:

```text
repository:
    read: approved repository
    write: deny

process:
    execute: deny

network:
    deny except approved model provider

model:
    provider: one approved provider
    excluded paths:
        - .env
        - **/*.pem
        - secrets/**

plugins:
    deny

publication:
    deny
```

---

## 30. Threat scenarios

### 30.1 Malicious repository instructions

Threat:

A source comment tells the model to exfiltrate credentials.

Control:

- repository content is evidence;
- worker has no credentials;
- model egress is scanned;
- network is denied except approved provider;
- credentials are not in context.

### 30.2 Model requests arbitrary shell

Threat:

The model proposes `curl` or shell execution.

Control:

- no shell tool exists by default;
- process capability absent;
- capability broker denies request.

### 30.3 Tool returns malicious instructions

Threat:

Tool output asks the model to invoke another privileged tool.

Control:

- output is untrusted;
- no authority is conveyed;
- later effects still require capability checks.

### 30.4 Cross-repository query

Threat:

A worker or caller requests another repository's index.

Control:

- scoped repository session;
- no generic repository ID queries;
- runtime validates session ownership.

### 30.5 Stale evidence after write

Threat:

The model reasons from pre-mutation source.

Control:

- workspace version advances;
- evidence invalidated synchronously;
- stale evidence cannot be admitted as current.

### 30.6 Database artifact leak

Threat:

A plugin reads model prompts from another run.

Control:

- no raw database handle;
- scoped artifact API;
- run ownership checks;
- audit event.

### 30.7 Compromised validator

Threat:

Validator attempts to publish directly.

Control:

- no publication capability;
- no publication credentials;
- separate publisher verifies validated artifact hash.

### 30.8 Compromised publisher

Threat:

Publisher modifies a different patch.

Control:

- validated patch hash binding;
- repository-scoped short-lived credential;
- publication audit.

---

## 31. Security invariants

1. Capabilities are denied by default.
2. Every effectful operation requires a capability decision.
3. Capabilities are scoped and non-transitive.
4. Models cannot grant authority.
5. Repository content cannot grant authority.
6. Tool output cannot grant authority.
7. Workers cannot mint capabilities.
8. Tool registration does not imply execution permission.
9. The agent runner does not hold publication credentials.
10. Remote model calls require egress authorization.
11. Network is denied by default.
12. Command execution is denied by default.
13. Arbitrary shell strings are unavailable by default.
14. Repository access occurs through scoped sessions.
15. Cross-run and cross-repository access are rejected.
16. Paths are normalized and checked at operation time.
17. Path escape is rejected.
18. Stale evidence cannot be treated as current.
19. Workers use private typed protocols.
20. Unknown protocol operations are rejected.
21. Embedded mode creates no public listener.
22. Third-party Python code runs out of process.
23. Secrets are not persisted in events or artifacts.
24. Secrets are not sent to model providers.
25. Validation uses immutable inputs.
26. Validation cannot publish.
27. Publication verifies validated artifact identity.
28. Security decisions are auditable.
29. Security failures fail closed.
30. Hosted tenant isolation does not rely only on logical database filters.

---

## 32. Open security questions

The security model is sufficient for implementation planning. Remaining details include:

- platform-specific sandbox mechanisms;
- Windows containment strategy;
- Linux namespace and seccomp profile;
- macOS sandbox strategy;
- secret-scanning implementation;
- local database encryption options;
- approval user experience;
- exact capability taxonomy;
- network mediation implementation;
- provider-specific egress policies;
- artifact access aggregation rules;
- trusted extension signing;
- security-profile distribution in hosted deployments;
- vulnerability disclosure and update model;
- dependency supply-chain policy.

These questions do not change the core security boundaries.
