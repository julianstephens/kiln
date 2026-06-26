# Kiln

Kiln is a secure, budget-aware runtime for repository-scale software engineering tasks performed with AI models.

The runtime—not the model—owns execution state, repository access, context selection, budgets, capabilities, validation, and termination. Models propose actions; Kiln decides whether those actions are permitted and records the resulting execution trace.

> **Status: pre-alpha**
>
> Kiln currently contains specifications, initial Python and Go runtime scaffolding, schema tooling, and the first repository-domain protocol contracts. End-to-end task execution is not yet implemented.

## Intended workflow

A Kiln run accepts:

* a repository
* a software-engineering task
* an approved model configuration
* a context policy
* a security profile
* resource budgets
* optional validation requirements

It is intended to produce:

* a grounded final answer
* an optional patch
* test and validation results
* an auditable execution trace
* resource-usage information
* an explicit terminal stop reason
* optional publication artifacts

The first implementation milestone is intentionally narrower: answer one read-only question about one local repository using structured repository evidence and explicit context and token budgets.

## Architecture

```text
Python application
        │
        ▼
Python SDK
        │ private process channel
        ▼
Go runtime
├── run coordination
├── agent loop
├── context management
├── budget enforcement
├── capability checks
├── model gateway
├── persistence
└── repository client
        │ private protocol
        ▼
Python repository worker
```

The public product is designed to behave like an embedded Python library. The authoritative Go runtime runs as a privately supervised child process, while repository parsing and indexing may run in an isolated Python worker.

### Core principles

* **The runtime is authoritative.** The model cannot grant itself permissions, spend unapproved budget, or declare a run complete.
* **Repository evidence is structured.** Files, symbols, source ranges, provenance, representations, and relevance are represented explicitly.
* **Retrieval and context admission are separate.** Retrieving evidence does not imply that the model will see it.
* **Capabilities are explicit.** Repository writes, command execution, network access, model calls, and publication are independently authorized.
* **Model and repository content are untrusted.**
* **Important decisions are observable and replayable.**
* **Repository state is versioned.** Evidence is tied to repository and workspace versions and may be invalidated after mutations.

## Repository layout

```text
.
├── ARCHITECTURE.md
├── docs/
│   ├── contracts.md
│   ├── persistence.md
│   ├── run-lifecycle.md
│   ├── security.md
│   └── vertical-slice.md
├── schemas/
│   ├── manifest.json
│   ├── common/
│   ├── repository/
│   ├── artifact/
│   └── fixtures/
├── devtools/
│   └── schema_tools/
├── python/
│   └── kiln/
├── go/
│   ├── cmd/
│   │   └── kiln-runtime/
│   └── internal/
├── Makefile
├── go.mod
└── pyproject.toml
```

## Requirements

Development currently expects:

* Python 3.13 or later
* [`uv`](https://docs.astral.sh/uv/)
* Go 1.25.5 or later
* `golangci-lint`
* GNU Make or a compatible implementation

## Development setup

```bash
git clone https://github.com/julianstephens/kiln.git
cd kiln

uv sync
make check
```

`make check` verifies formatting, runs linters and tests, builds the Python and Go artifacts, and validates the schema set.

Individual commands are also available:

```bash
make help
make format
make format-check
make lint
make test
make build
make validate-schemas
make clean
```

Build outputs are written under:

```text
dist/
├── python/
└── bin/
    └── kiln-runtime
```

## Schema contracts

Language-neutral contracts live under `schemas/`.

Each schema uses:

* JSON Schema draft 2020-12
* a stable `$id`
* an explicit schema-set release
* a major compatibility version
* explicit required and optional fields
* explicit unknown-property behavior

Schema IDs follow this form:

```text
https://kiln.cyborgdev.cloud/schemas/<domain>/v<major>/<contract>.schema.json
```

The directory layout is:

```text
schemas/
├── manifest.json
├── <domain>/
│   └── v<major>/
│       └── <contract>.schema.json
└── fixtures/
    ├── valid/
    │   └── v<major>/
    │       └── <domain>-<contract>-<case>.json
    └── invalid/
        └── v<major>/
            └── <domain>-<contract>-<case>.json
```

## Documentation

Start with:

* [`ARCHITECTURE.md`](ARCHITECTURE.md) — architectural boundaries and component responsibilities
* [`docs/vertical-slice.md`](docs/vertical-slice.md) — the first end-to-end milestone
* [`docs/contracts.md`](docs/contracts.md) — contract ownership and compatibility rules
* [`docs/run-lifecycle.md`](docs/run-lifecycle.md) — lifecycle states and transitions
* [`docs/security.md`](docs/security.md) — trust and capability model
* [`docs/persistence.md`](docs/persistence.md) — state, event, and artifact persistence
* [`schemas/README.md`](schemas/README.md) — schema-specific conventions

## Near-term roadmap

1. Complete the shared first-slice schema domains.
2. Implement the runtime and repository protocol handlers.
3. Implement repository preparation, search, source retrieval, and one graph relation.
4. Add deterministic context admission and budget enforcement.
5. Add one approved model adapter.
6. Persist events, artifacts, usage, and terminal outcomes.
7. Complete the read-only vertical slice.
8. Add mutation, validation, and publication only after the read-only boundary is proven.
