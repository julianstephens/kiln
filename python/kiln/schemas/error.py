"""
Generated Pydantic v2 models for Kiln JSON Schemas.

Do not edit this package by hand. Regenerate with:

    uv run generatemodels
"""

from __future__ import annotations

from enum import StrEnum
from typing import Annotated, Any

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field

from . import diagnostic, diagnostic_log_reference, error_category, reference


class Code(StrEnum):
    validation_failed = "validation_failed"
    validation_error = "validation_error"
    capability_denied = "capability_denied"
    capability_unavailable = "capability_unavailable"
    repository_unavailable = "repository_unavailable"
    repository_dirty = "repository_dirty"
    repository_preparation_failed = "repository_preparation_failed"
    repository_session_invalid = "repository_session_invalid"
    tool_failed = "tool_failed"
    tool_timed_out = "tool_timed_out"
    tool_result_invalid = "tool_result_invalid"
    external_operation_failed = "external_operation_failed"
    external_operation_timed_out = "external_operation_timed_out"
    external_operation_result_invalid = "external_operation_result_invalid"
    output_production_failed = "output_production_failed"
    artifact_write_failed = "artifact_write_failed"
    answer_assembly_failed = "answer_assembly_failed"
    patch_generation_failed = "patch_generation_failed"
    runtime_interrupted = "runtime_interrupted"
    worker_interrupted = "worker_interrupted"
    shutdown_interrupted = "shutdown_interrupted"
    lease_lost = "lease_lost"
    internal_error = "internal_error"
    invariant_violation = "invariant_violation"
    persistence_failed = "persistence_failed"


class Severity(StrEnum):
    warning = "warning"
    error = "error"
    fatal = "fatal"


class LifecycleState(StrEnum):
    created = "created"
    initializing = "initializing"
    preparing_repository = "preparing_repository"
    running = "running"
    producing_output = "producing_output"
    validating = "validating"
    completed = "completed"
    failed = "failed"
    canceled = "canceled"
    exhausted = "exhausted"


class Kind(StrEnum):
    repository_preparation = "repository_preparation"
    repository_query = "repository_query"
    context_plan = "context_plan"
    model_invocation = "model_invocation"
    tool_call = "tool_call"
    external_job = "external_job"
    output_production = "output_production"
    validation = "validation"
    recovery = "recovery"


class OperationReference(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    kind: Kind
    id: Annotated[str, Field(min_length=1)]
    correlation_id: Annotated[str | None, Field(min_length=1)] = None


class Cause(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    error_id: Annotated[str | None, Field(min_length=1)] = None
    code: Annotated[str | None, Field(min_length=1)] = None
    message: Annotated[str | None, Field(min_length=1)] = None


class Category(StrEnum):
    protocol = "protocol"
    authorization = "authorization"
    session = "session"
    version = "version"
    repository = "repository"
    indexing = "indexing"
    parsing = "parsing"
    search = "search"
    graph = "graph"
    representation = "representation"
    resource = "resource"
    persistence = "persistence"
    cancellation = "cancellation"
    internal = "internal"


class Schema(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    code: Annotated[str, Field(min_length=1)]
    category: Category
    message: Annotated[str, Field(min_length=1)]
    retryable: bool
    operation_id: Annotated[str, Field(min_length=1)]
    repository_session_id: Annotated[str, Field(min_length=1)]
    repository_version: dict[str, Any]
    workspace_version: dict[str, Any]
    diagnostics: list[diagnostic.Schema]
    artifact_references: list[diagnostic_log_reference.Schema]
    cause_error_id: Annotated[str | None, Field(min_length=1)] = None


class CategoryModel(StrEnum):
    invalid_request = "invalid_request"
    authentication = "authentication"
    authorization = "authorization"
    rate_limited = "rate_limited"
    quota_exceeded = "quota_exceeded"
    timeout = "timeout"
    provider_unavailable = "provider_unavailable"
    model_unavailable = "model_unavailable"
    content_filter = "content_filter"
    egress_denied = "egress_denied"
    context_length_exceeded = "context_length_exceeded"
    adapter_error = "adapter_error"
    canceled = "canceled"
    unknown = "unknown"


class SchemaModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    error_id: Annotated[
        str, Field(description="Stable identity for this model error.", min_length=1)
    ]
    category: Annotated[
        CategoryModel, Field(description="Provider-neutral model error category.")
    ]
    code: Annotated[
        str,
        Field(
            description="Provider-neutral or adapter-normalized error code.",
            min_length=1,
        ),
    ]
    provider_code: Annotated[
        str | None,
        Field(
            description="Provider-specific error code, when safe to expose.",
            min_length=1,
        ),
    ] = None
    message: Annotated[
        str,
        Field(
            description="Human-readable provider-neutral error message.", min_length=1
        ),
    ]
    retryable: Annotated[
        bool, Field(description="Whether the model invocation may be retried.")
    ]
    retry_after_seconds: Annotated[
        int | None,
        Field(description="Suggested retry delay in seconds, when available.", ge=0),
    ] = None
    model_id: Annotated[
        str | None,
        Field(
            description="Model identifier associated with the failure, when known.",
            min_length=1,
        ),
    ] = None
    provider_id: Annotated[
        str | None,
        Field(
            description="Provider associated with the failure, when known.",
            min_length=1,
        ),
    ] = None
    model_invocation_id: Annotated[
        str | None,
        Field(
            description="Model invocation associated with the failure, when known.",
            min_length=1,
        ),
    ] = None
    partial_response_artifact_reference: Annotated[
        reference.Schema | None,
        Field(
            description="Artifact reference for partial model response content, when available."
        ),
    ] = None
    diagnostic_artifact_reference: Annotated[
        diagnostic_log_reference.Schema | None,
        Field(
            description="Artifact reference for model diagnostic details, when available."
        ),
    ] = None


class SchemaModel1(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    error_id: Annotated[
        str, Field(description="Stable identifier for this error record.", min_length=1)
    ]
    run_id: Annotated[
        str,
        Field(
            description="Identifier of the run associated with this error.",
            min_length=1,
        ),
    ]
    category: Annotated[
        error_category.Schema, Field(description="Broad class of run error.")
    ]
    code: Annotated[
        Code, Field(description="Specific machine-readable run error code.")
    ]
    message: Annotated[
        str, Field(description="Human-readable explanation of the error.", min_length=1)
    ]
    severity: Annotated[
        Severity | None, Field(description="Severity of the error.")
    ] = "error"
    lifecycle_state: Annotated[
        LifecycleState | None,
        Field(description="Run lifecycle state in which the error occurred."),
    ] = None
    operation_reference: Annotated[
        OperationReference | None,
        Field(
            description="Optional reference to the operation that produced the error."
        ),
    ] = None
    source: Annotated[
        str | None,
        Field(
            description="Component or subsystem that reported the error.", min_length=1
        ),
    ] = None
    cause: Annotated[
        Cause | None,
        Field(description="Optional nested causal error reference or summary."),
    ] = None
    details: Annotated[
        dict[str, Any] | None,
        Field(
            description="Optional structured diagnostic details. Intended for machine-readable context, not arbitrary logs."
        ),
    ] = None
    artifact_references: Annotated[
        list[reference.Schema] | None,
        Field(
            description="Artifacts containing supporting diagnostics, logs, reports, or partial outputs."
        ),
    ] = None
    retryable: Annotated[
        bool | None, Field(description="Whether retry may be attempted by policy.")
    ] = None
    occurred_at: Annotated[AwareDatetime, Field(description="When the error occurred.")]
