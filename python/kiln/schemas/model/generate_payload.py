"""
Generated Pydantic v2 models for Kiln JSON Schemas.

Do not edit this package by hand. Regenerate with:

    uv run generatemodels
"""

from __future__ import annotations

from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, RootModel

from . import reference, rendered


class StopSequence(RootModel[str]):
    root: Annotated[str, Field(min_length=1)]


class ReasoningEffort(StrEnum):
    minimal = "minimal"
    low = "low"
    medium = "medium"
    high = "high"


class GenerationParameters(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    temperature: Annotated[
        float | None, Field(description="Sampling temperature.", ge=0.0)
    ] = None
    top_p: Annotated[
        float | None,
        Field(description="Nucleus sampling probability mass.", ge=0.0, le=1.0),
    ] = None
    max_output_tokens: Annotated[
        int,
        Field(
            description="Maximum output tokens allowed for this generation request.",
            ge=1,
        ),
    ]
    stop_sequences: Annotated[
        list[StopSequence] | None,
        Field(
            description="Stop sequences that should terminate generation.", min_length=1
        ),
    ] = None
    seed: Annotated[
        int | None,
        Field(description="Determinism seed, when supported by the model adapter."),
    ] = None
    reasoning_effort: Annotated[
        ReasoningEffort | None,
        Field(description="Provider-neutral reasoning effort hint."),
    ] = None


class ResponseMode(StrEnum):
    answer = "answer"
    patch = "patch"
    answer_with_patch = "answer_with_patch"
    report = "report"
    tool_call = "tool_call"
    structured_json = "structured_json"


class AllowedToolName(RootModel[str]):
    root: Annotated[str, Field(min_length=1)]


class ResponseConstraints(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    response_mode: Annotated[
        ResponseMode, Field(description="Expected response shape.")
    ]
    required_content_type: Annotated[
        str | None,
        Field(
            description="Required response content type, when applicable.", min_length=1
        ),
    ] = None
    json_schema_reference: Annotated[
        reference.Schema | None,
        Field(
            description="Artifact or schema reference for structured JSON output constraints."
        ),
    ] = None
    citation_required: Annotated[
        bool | None,
        Field(description="Whether citations are required in the generated result."),
    ] = None
    max_answer_chars: Annotated[
        int | None, Field(description="Maximum answer length in characters.", ge=1)
    ] = None
    allow_tool_calls: Annotated[
        bool | None, Field(description="Whether the response may request tool calls.")
    ] = None
    allowed_tool_names: Annotated[
        list[AllowedToolName] | None,
        Field(description="Tool names the model is allowed to request.", min_length=1),
    ] = None


class Schema(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    model_id: Annotated[
        str,
        Field(
            description="Provider-neutral or adapter-local model identifier requested for generation.",
            min_length=1,
        ),
    ]
    provider_id: Annotated[
        str,
        Field(
            description="Provider identifier, when generation is routed through an external provider.",
            min_length=1,
        ),
    ]
    local_adapter_id: Annotated[
        str | None,
        Field(
            description="Local adapter identifier, when generation is routed through a local model adapter.",
            min_length=1,
        ),
    ] = None
    rendered_context: Annotated[
        rendered.Schema,
        Field(description="Rendered context consumed by this generation request."),
    ]
    user_question: Annotated[
        str | None,
        Field(
            description="User question or instruction for generation, when not already fully represented by rendered context.",
            min_length=1,
        ),
    ] = None
    generation_parameters: Annotated[
        GenerationParameters,
        Field(description="Provider-neutral generation parameters."),
    ]
    response_constraints: Annotated[
        ResponseConstraints,
        Field(description="Constraints on the response the model should produce."),
    ]
    request_artifact_reference: Annotated[
        reference.Schema | None,
        Field(
            description="Artifact reference for the fully rendered provider request, when materialized."
        ),
    ] = None


class SchemaModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    model_id: Annotated[
        str,
        Field(
            description="Provider-neutral or adapter-local model identifier requested for generation.",
            min_length=1,
        ),
    ]
    provider_id: Annotated[
        str | None,
        Field(
            description="Provider identifier, when generation is routed through an external provider.",
            min_length=1,
        ),
    ] = None
    local_adapter_id: Annotated[
        str,
        Field(
            description="Local adapter identifier, when generation is routed through a local model adapter.",
            min_length=1,
        ),
    ]
    rendered_context: Annotated[
        rendered.Schema,
        Field(description="Rendered context consumed by this generation request."),
    ]
    user_question: Annotated[
        str | None,
        Field(
            description="User question or instruction for generation, when not already fully represented by rendered context.",
            min_length=1,
        ),
    ] = None
    generation_parameters: Annotated[
        GenerationParameters,
        Field(description="Provider-neutral generation parameters."),
    ]
    response_constraints: Annotated[
        ResponseConstraints,
        Field(description="Constraints on the response the model should produce."),
    ]
    request_artifact_reference: Annotated[
        reference.Schema | None,
        Field(
            description="Artifact reference for the fully rendered provider request, when materialized."
        ),
    ] = None


class SchemaModel1(RootModel[Schema | SchemaModel]):
    root: Annotated[
        Schema | SchemaModel,
        Field(
            description="Provider-neutral payload for model generation, including model identity, rendered context, user question, generation parameters, and response constraints.",
            title="Kiln model generate payload",
        ),
    ]
