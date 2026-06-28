"""
Generated Pydantic v2 models for Kiln JSON Schemas.

Do not edit this package by hand. Regenerate with:

    uv run generatemodels
"""

from __future__ import annotations

from enum import StrEnum
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from . import diagnostic, diagnostic_log_reference, identifier, reference
from . import source_range as source_range_1
from . import usage as usage_1


class Status(StrEnum):
    ok = "ok"
    not_found = "not_found"
    invalid_request = "invalid_request"
    denied = "denied"
    stale_session = "stale_session"
    conflict = "conflict"
    canceled = "canceled"
    exhausted = "exhausted"
    retryable_error = "retryable_error"
    fatal_error = "fatal_error"


class Schema(BaseModel):
    protocol_version: Literal["1"]
    request_id: Annotated[str, Field(min_length=1)]
    operation: Annotated[str, Field(min_length=1)]
    status: Status
    correlation_id: Annotated[str | None, Field(min_length=1)] = None
    result: dict[str, Any] | None = None
    error: dict[str, Any] | None = None


class ToolCallRequests(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    tool_call_id: Annotated[
        str,
        Field(
            description="Stable identity for this requested tool call.", min_length=1
        ),
    ]
    tool_name: Annotated[
        str, Field(description="Name of the requested tool.", min_length=1)
    ]
    arguments: Annotated[
        dict[str, Any],
        Field(description="Inline tool-call arguments for small argument payloads."),
    ]
    arguments_artifact_reference: Annotated[
        reference.Schema | None,
        Field(
            description="Artifact reference for large or sensitive tool-call arguments."
        ),
    ] = None


class ToolCallRequestsModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    tool_call_id: Annotated[
        str,
        Field(
            description="Stable identity for this requested tool call.", min_length=1
        ),
    ]
    tool_name: Annotated[
        str, Field(description="Name of the requested tool.", min_length=1)
    ]
    arguments: Annotated[
        dict[str, Any] | None,
        Field(description="Inline tool-call arguments for small argument payloads."),
    ] = None
    arguments_artifact_reference: Annotated[
        reference.Schema,
        Field(
            description="Artifact reference for large or sensitive tool-call arguments."
        ),
    ]


class FinishReason(StrEnum):
    stop = "stop"
    length = "length"
    tool_call = "tool_call"
    content_filter = "content_filter"
    canceled = "canceled"
    unknown = "unknown"


class Citation(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    citation_id: Annotated[
        str, Field(description="Stable identity for this citation.", min_length=1)
    ]
    source_reference: Annotated[
        reference.Schema, Field(description="Artifact reference for the cited source.")
    ]
    quoted_text: Annotated[
        str | None,
        Field(
            description="Quoted text supporting the generated content, when retained.",
            min_length=1,
        ),
    ] = None
    source_range: Annotated[
        source_range_1.Schema | None,
        Field(
            description="Source range supporting the generated content, when applicable."
        ),
    ] = None
    confidence: Annotated[
        float | None,
        Field(
            description="Confidence that this citation supports the associated generated content.",
            ge=0.0,
            le=1.0,
        ),
    ] = None


class GroundingStatus(StrEnum):
    grounded = "grounded"
    partially_grounded = "partially_grounded"
    ungrounded = "ungrounded"
    not_evaluated = "not_evaluated"


class SupportMetadata(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    grounding_status: GroundingStatus | None = None
    support_artifact_references: Annotated[
        list[reference.Schema] | None, Field(min_length=1)
    ] = None
    unsupported_claim_count: Annotated[int | None, Field(ge=0)] = None


class ToolCallRequestsModel1(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    tool_call_id: Annotated[
        str,
        Field(
            description="Stable identity for this requested tool call.", min_length=1
        ),
    ]
    tool_name: Annotated[
        str, Field(description="Name of the requested tool.", min_length=1)
    ]
    arguments: Annotated[
        dict[str, Any],
        Field(description="Inline tool-call arguments for small argument payloads."),
    ]
    arguments_artifact_reference: Annotated[
        reference.Schema | None,
        Field(
            description="Artifact reference for large or sensitive tool-call arguments."
        ),
    ] = None


class ToolCallRequestsModel2(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    tool_call_id: Annotated[
        str,
        Field(
            description="Stable identity for this requested tool call.", min_length=1
        ),
    ]
    tool_name: Annotated[
        str, Field(description="Name of the requested tool.", min_length=1)
    ]
    arguments: Annotated[
        dict[str, Any] | None,
        Field(description="Inline tool-call arguments for small argument payloads."),
    ] = None
    arguments_artifact_reference: Annotated[
        reference.Schema,
        Field(
            description="Artifact reference for large or sensitive tool-call arguments."
        ),
    ]


class ToolCallRequestsModel3(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    tool_call_id: Annotated[
        str,
        Field(
            description="Stable identity for this requested tool call.", min_length=1
        ),
    ]
    tool_name: Annotated[
        str, Field(description="Name of the requested tool.", min_length=1)
    ]
    arguments: Annotated[
        dict[str, Any],
        Field(description="Inline tool-call arguments for small argument payloads."),
    ]
    arguments_artifact_reference: Annotated[
        reference.Schema | None,
        Field(
            description="Artifact reference for large or sensitive tool-call arguments."
        ),
    ] = None


class ToolCallRequestsModel4(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    tool_call_id: Annotated[
        str,
        Field(
            description="Stable identity for this requested tool call.", min_length=1
        ),
    ]
    tool_name: Annotated[
        str, Field(description="Name of the requested tool.", min_length=1)
    ]
    arguments: Annotated[
        dict[str, Any] | None,
        Field(description="Inline tool-call arguments for small argument payloads."),
    ] = None
    arguments_artifact_reference: Annotated[
        reference.Schema,
        Field(
            description="Artifact reference for large or sensitive tool-call arguments."
        ),
    ]


class ToolCallRequestsModel5(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    tool_call_id: Annotated[
        str,
        Field(
            description="Stable identity for this requested tool call.", min_length=1
        ),
    ]
    tool_name: Annotated[
        str, Field(description="Name of the requested tool.", min_length=1)
    ]
    arguments: Annotated[
        dict[str, Any],
        Field(description="Inline tool-call arguments for small argument payloads."),
    ]
    arguments_artifact_reference: Annotated[
        reference.Schema | None,
        Field(
            description="Artifact reference for large or sensitive tool-call arguments."
        ),
    ] = None


class ToolCallRequestsModel6(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    tool_call_id: Annotated[
        str,
        Field(
            description="Stable identity for this requested tool call.", min_length=1
        ),
    ]
    tool_name: Annotated[
        str, Field(description="Name of the requested tool.", min_length=1)
    ]
    arguments: Annotated[
        dict[str, Any] | None,
        Field(description="Inline tool-call arguments for small argument payloads."),
    ] = None
    arguments_artifact_reference: Annotated[
        reference.Schema,
        Field(
            description="Artifact reference for large or sensitive tool-call arguments."
        ),
    ]


class Category(StrEnum):
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


class Error(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    error_id: Annotated[
        str, Field(description="Stable identity for this model error.", min_length=1)
    ]
    category: Annotated[
        Category, Field(description="Provider-neutral model error category.")
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


class CategoryModel(StrEnum):
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


class ErrorModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    code: Annotated[str, Field(min_length=1)]
    category: CategoryModel
    message: Annotated[str, Field(min_length=1)]
    retryable: bool
    operation_id: Annotated[str, Field(min_length=1)]
    repository_session_id: Annotated[str, Field(min_length=1)]
    repository_version: dict[str, Any]
    workspace_version: dict[str, Any]
    diagnostics: list[diagnostic.Schema]
    artifact_references: list[diagnostic_log_reference.Schema]
    cause_error_id: Annotated[str | None, Field(min_length=1)] = None


class SchemaModel(Schema):
    operation: Annotated[str | None, Field(min_length=1, pattern="^repository\\.")] = (
        None
    )
    repository: identifier.Schema | None = None
    error: Annotated[
        ErrorModel | None,
        Field(
            description="Repository-protocol error details including category, diagnostics, operation context, and related artifacts.",
            title="Kiln repository error",
        ),
    ] = None
    usage: usage_1.SchemaModel | None = None
    diagnostics: list[diagnostic.Schema] | None = None
    artifact_references: list[reference.Schema]


class Result(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    answer: Annotated[
        str,
        Field(
            description="Generated textual answer, when returned inline.", min_length=1
        ),
    ]
    answer_artifact_reference: Annotated[
        reference.Schema | None,
        Field(
            description="Artifact reference for generated answer content, when not returned inline."
        ),
    ] = None
    structured_output: Annotated[
        dict[str, Any] | None,
        Field(
            description="Provider-neutral structured output, when the response mode requested structured JSON."
        ),
    ] = None
    tool_call_requests: Annotated[
        list[ToolCallRequests | ToolCallRequestsModel] | None,
        Field(description="Tool calls requested by the model.", min_length=1),
    ] = None
    finish_reason: Annotated[
        FinishReason, Field(description="Provider-neutral reason generation stopped.")
    ]
    usage: usage_1.SchemaModel1
    response_artifact_reference: Annotated[
        reference.Schema | None,
        Field(description="Artifact reference for the raw model response."),
    ] = None
    citations: Annotated[
        list[Citation] | None,
        Field(
            description="Structured citations supporting generated content.",
            min_length=1,
        ),
    ] = None
    support_metadata: Annotated[
        SupportMetadata | None,
        Field(
            description="Provider-neutral support metadata for generated claims, citations, or retrieval grounding."
        ),
    ] = None


class ResultModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    answer: Annotated[
        str | None,
        Field(
            description="Generated textual answer, when returned inline.", min_length=1
        ),
    ] = None
    answer_artifact_reference: Annotated[
        reference.Schema,
        Field(
            description="Artifact reference for generated answer content, when not returned inline."
        ),
    ]
    structured_output: Annotated[
        dict[str, Any] | None,
        Field(
            description="Provider-neutral structured output, when the response mode requested structured JSON."
        ),
    ] = None
    tool_call_requests: Annotated[
        list[ToolCallRequestsModel1 | ToolCallRequestsModel2] | None,
        Field(description="Tool calls requested by the model.", min_length=1),
    ] = None
    finish_reason: Annotated[
        FinishReason, Field(description="Provider-neutral reason generation stopped.")
    ]
    usage: usage_1.SchemaModel1
    response_artifact_reference: Annotated[
        reference.Schema | None,
        Field(description="Artifact reference for the raw model response."),
    ] = None
    citations: Annotated[
        list[Citation] | None,
        Field(
            description="Structured citations supporting generated content.",
            min_length=1,
        ),
    ] = None
    support_metadata: Annotated[
        SupportMetadata | None,
        Field(
            description="Provider-neutral support metadata for generated claims, citations, or retrieval grounding."
        ),
    ] = None


class ResultModel1(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    answer: Annotated[
        str | None,
        Field(
            description="Generated textual answer, when returned inline.", min_length=1
        ),
    ] = None
    answer_artifact_reference: Annotated[
        reference.Schema | None,
        Field(
            description="Artifact reference for generated answer content, when not returned inline."
        ),
    ] = None
    structured_output: Annotated[
        dict[str, Any],
        Field(
            description="Provider-neutral structured output, when the response mode requested structured JSON."
        ),
    ]
    tool_call_requests: Annotated[
        list[ToolCallRequestsModel3 | ToolCallRequestsModel4] | None,
        Field(description="Tool calls requested by the model.", min_length=1),
    ] = None
    finish_reason: Annotated[
        FinishReason, Field(description="Provider-neutral reason generation stopped.")
    ]
    usage: usage_1.SchemaModel1
    response_artifact_reference: Annotated[
        reference.Schema | None,
        Field(description="Artifact reference for the raw model response."),
    ] = None
    citations: Annotated[
        list[Citation] | None,
        Field(
            description="Structured citations supporting generated content.",
            min_length=1,
        ),
    ] = None
    support_metadata: Annotated[
        SupportMetadata | None,
        Field(
            description="Provider-neutral support metadata for generated claims, citations, or retrieval grounding."
        ),
    ] = None


class ResultModel2(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    answer: Annotated[
        str | None,
        Field(
            description="Generated textual answer, when returned inline.", min_length=1
        ),
    ] = None
    answer_artifact_reference: Annotated[
        reference.Schema | None,
        Field(
            description="Artifact reference for generated answer content, when not returned inline."
        ),
    ] = None
    structured_output: Annotated[
        dict[str, Any] | None,
        Field(
            description="Provider-neutral structured output, when the response mode requested structured JSON."
        ),
    ] = None
    tool_call_requests: Annotated[
        list[ToolCallRequestsModel5 | ToolCallRequestsModel6],
        Field(description="Tool calls requested by the model.", min_length=1),
    ]
    finish_reason: Annotated[
        FinishReason, Field(description="Provider-neutral reason generation stopped.")
    ]
    usage: usage_1.SchemaModel1
    response_artifact_reference: Annotated[
        reference.Schema | None,
        Field(description="Artifact reference for the raw model response."),
    ] = None
    citations: Annotated[
        list[Citation] | None,
        Field(
            description="Structured citations supporting generated content.",
            min_length=1,
        ),
    ] = None
    support_metadata: Annotated[
        SupportMetadata | None,
        Field(
            description="Provider-neutral support metadata for generated claims, citations, or retrieval grounding."
        ),
    ] = None


class SchemaModel1(Schema):
    operation: Annotated[str | None, Field(min_length=1, pattern="^model\\.")] = None
    result: Annotated[
        Result | ResultModel | ResultModel1 | ResultModel2 | None,
        Field(
            description="Provider-neutral result of model generation, including generated content, finish reason, usage, and optional support metadata.",
            title="Kiln model generate result",
        ),
    ] = None
    error: Annotated[
        Error | None,
        Field(
            description="Provider-neutral model failure body for model protocol responses and model invocation events.",
            title="Kiln model error",
        ),
    ] = None
    usage: usage_1.SchemaModel1 | None = None
    artifact_references: Annotated[
        list[reference.Schema] | None, Field(min_length=1)
    ] = None
