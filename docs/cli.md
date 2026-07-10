# Kiln CLI

## Status

Draft

## Purpose

The Kiln CLI is a first-class public interface alongside the Python SDK.

The SDK is the embedding interface for Python applications and runtime builders.
The CLI is the interoperability interface for developers, terminals, scripts, CI systems, and future IDE integrations.

Both interfaces operate on the same durable Kiln runs and must expose the same underlying semantics. The CLI must not implement a second run coordinator, lifecycle model, event system, or result model.

---

## 1. Product boundary

```text
Python application ── Python SDK ──┐
                                  │
Terminal / IDE / CI ── Kiln CLI ──┼── Python runtime client
                                  │
                                  ▼
                         private Go runtime
```

The CLI is implemented in Python and uses the public Python SDK or its shared public client layer.

The private Python-to-Go runtime protocol remains an implementation boundary. CLI users and IDE clients do not speak it directly.

---

## 2. First-slice goals

The initial read-only vertical slice is complete only when both of these workflows succeed:

```python
result = agent.run("Explain the repository indexing flow")
```

```bash
kiln run --repository . --task "Explain the repository indexing flow"
```

The two surfaces must produce equivalent run specifications, durable run state, event history, terminal status, usage, and result semantics.

---

## 3. Initial command surface

The first slice requires:

```text
kiln run
kiln runs list
kiln runs show <run-id>
kiln runs events <run-id>
kiln runs cancel <run-id>
kiln runs result <run-id>
```

The first implementation may keep `runs list` intentionally narrow, but durable runs must be inspectable without retaining the process or object that created them.

### 3.1 `kiln run`

Creates a durable run and, by default, follows it until terminal completion.

Required inputs:

- repository path;
- task text or task file;
- model configuration;
- budgets;
- security profile or approved default.

Required behavior:

- submit the same `RunSpecification` used by the SDK;
- print a stable run identity immediately after creation;
- stream progress without treating console text as authoritative state;
- propagate user cancellation;
- return a process exit status derived from the terminal run outcome;
- preserve the run for later inspection.

### 3.2 Inspection commands

Inspection commands read durable state through the same runtime methods used by the SDK.

They must not query the installation database directly.

### 3.3 Cancellation

`kiln runs cancel` requests authorized run cancellation by durable run identity.

Closing the terminal or interrupting a following client must not silently redefine the run's terminal state. The CLI may request cancellation according to command policy, detach, or report that the final disposition is unknown.

---

## 4. Output modes

The CLI supports two distinct output modes.

### 4.1 Human output

Human output is concise and presentation-oriented.

It may include:

- current lifecycle phase;
- bounded progress summaries;
- final answer;
- terminal status and stop reason;
- usage summary;
- run identity for later inspection.

Human output is not a stable integration protocol.

### 4.2 Machine output

Machine output uses newline-delimited JSON.

```bash
kiln run ... --output jsonl
```

Each line is one bounded CLI message. Messages contain stable CLI envelope fields and either:

- a validated Kiln event projection;
- a materialized run-state projection;
- a terminal `RunResult` projection;
- a CLI-local error that occurred before a run existed.

Machine output must:

- remain parseable when progress is enabled;
- never mix human diagnostics into stdout;
- write diagnostics to stderr;
- preserve run, event sequence, and artifact identities;
- declare schema or format version;
- make truncation explicit.

The CLI envelope is a public presentation contract. It is not the authoritative event store and must not invent competing domain events.

---

## 5. Exit status

The CLI defines stable exit classes rather than exposing raw runtime process exit codes.

Initial classes:

| Exit class | Meaning |
| --- | --- |
| success | Run completed successfully. |
| failed | Run reached terminal `failed`. |
| cancelled | Run reached terminal `cancelled`. |
| exhausted | Run reached terminal `exhausted`. |
| invalid_usage | CLI arguments or local configuration were invalid before run creation. |
| client_failure | The CLI could not determine or retrieve the durable run outcome. |

Exact numeric values are an implementation decision but become compatibility-stable once published.

---

## 6. Shared SDK and CLI semantics

The SDK and CLI must share:

- run-specification construction and validation;
- runtime startup and connection behavior;
- durable run creation;
- event sequence and cursor semantics;
- cancellation semantics;
- result retrieval;
- structured Kiln errors;
- configuration resolution;
- model, budget, and security-profile interpretation.

The CLI may add presentation defaults, argument parsing, terminal signal handling, and output formatting.

It must not add domain behavior unavailable through the SDK.

The SDK must not depend on CLI parsing or console behavior.

---

## 7. Configuration precedence

The first slice should define one deterministic precedence order:

```text
explicit command arguments
    > explicitly selected configuration file
    > workspace configuration
    > user installation configuration
    > built-in defaults
```

The effective configuration used to build the run specification must be inspectable and must not contain raw secrets.

CLI environment variables may identify secret references or approved configuration values, but broad environment inheritance must not become runtime authority.

---

## 8. IDE integration boundary

Future IDE integrations should launch the CLI in machine-output mode or use the same public Python client layer.

The first slice does not require a VS Code or JetBrains extension.

It does require that the CLI be usable as an integration host:

- stable machine-readable stdout;
- separate stderr diagnostics;
- durable run identities;
- reconnectable event inspection;
- cancellation by run identity;
- result retrieval after the creating process exits.

This prevents future editor extensions from depending on the private Go runtime protocol.

---

## 9. Security

The CLI grants no authority by itself.

It requests runs under trusted local configuration and the runtime's capability model.

The CLI must:

- avoid printing secrets;
- avoid embedding publication or model credentials in run specifications;
- preserve protected-path and model-egress decisions;
- use the private supervised runtime rather than exposing a public listener;
- keep machine stdout protocol-clean;
- treat repository and model content as untrusted data.

---

## 10. First-slice acceptance

The CLI portion of the first slice is accepted when:

1. `kiln run` completes the canonical read-only repository question through the real runtime;
2. the equivalent Python SDK call produces semantically equivalent durable records and result fields;
3. JSONL output can be consumed without parsing human text;
4. a run can be inspected and its result retrieved by identity from a separate CLI invocation;
5. cancellation can be requested from a separate CLI invocation;
6. terminal outcomes map to documented exit classes;
7. stdout remains clean in machine mode;
8. unexpected runtime or client failure preserves the durable run identity and reports whether the final disposition is known;
9. CLI integration tests run in the full acceptance suite;
10. no CLI code bypasses runtime lifecycle, persistence, capability, budget, or event boundaries.

---

## 11. Deferred CLI capabilities

Deferred beyond the first read-only slice:

- interactive chat sessions;
- patch application;
- native diff review;
- validation presentation;
- publication commands;
- long-running local daemon mode;
- plugin discovery;
- MCP server mode;
- IDE-specific extension packages;
- remote hosted-run submission.

These capabilities should extend the durable run and artifact model rather than replace it.
