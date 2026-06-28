"""
Generated Pydantic v2 models for Kiln JSON Schemas.

Do not edit this package by hand. Regenerate with:

    uv run generatemodels
"""

from __future__ import annotations

from enum import StrEnum
from typing import Annotated

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field

from . import reference
from . import usage as usage_1


class FinishReason(StrEnum):
    stop = "stop"
    length = "length"
    tool_call = "tool_call"
    content_filter = "content_filter"
    error = "error"
    unknown = "unknown"


class Usage(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    input_tokens: Annotated[int, Field(ge=0)]
    output_tokens: Annotated[int, Field(ge=0)]
    cached_input_tokens: Annotated[int | None, Field(ge=0)] = None
    reasoning_tokens: Annotated[int | None, Field(ge=0)] = None
    total_tokens: Annotated[int | None, Field(ge=0)] = None


class Schema(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    model_invocation_id: Annotated[
        str, Field(description="Model invocation that completed.", min_length=1)
    ]
    response_artifact_reference: Annotated[
        reference.Schema,
        Field(description="Artifact reference for the raw model response."),
    ]
    finish_reason: Annotated[
        FinishReason, Field(description="Provider or adapter normalized finish reason.")
    ]
    usage: Annotated[
        Usage, Field(description="Model usage recorded for this invocation.")
    ]
    budget_usage: Annotated[
        usage_1.Schema | None,
        Field(description="Budget usage committed for this model invocation."),
    ] = None
    latency_ms: Annotated[
        int | None,
        Field(description="Elapsed invocation latency in milliseconds.", ge=0),
    ] = None
    completed_at: Annotated[
        AwareDatetime, Field(description="When the model invocation completed.")
    ]
