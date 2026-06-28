"""
Generated Pydantic v2 models for Kiln JSON Schemas.

Do not edit this package by hand. Regenerate with:

    uv run generatemodels
"""

from __future__ import annotations

from enum import StrEnum
from typing import Annotated, Any

from pydantic import BaseModel, ConfigDict, Field, RootModel

from . import reference
from . import source_range as source_range_1
from . import usage as usage_1


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


class Schema(BaseModel):
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


class SchemaModel(BaseModel):
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


class SchemaModel1(BaseModel):
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


class SchemaModel2(BaseModel):
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


class SchemaModel3(RootModel[Schema | SchemaModel | SchemaModel1 | SchemaModel2]):
    root: Annotated[
        Schema | SchemaModel | SchemaModel1 | SchemaModel2,
        Field(
            description="Provider-neutral result of model generation, including generated content, finish reason, usage, and optional support metadata.",
            title="Kiln model generate result",
        ),
    ]
