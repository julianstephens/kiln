"""
Generated Pydantic v2 models for Kiln JSON Schemas.

Do not edit this package by hand. Regenerate with:

    uv run generatemodels
"""

from __future__ import annotations

from enum import StrEnum
from typing import Annotated

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field


class UsageScope(StrEnum):
    run = "run"
    turn = "turn"
    operation = "operation"
    component = "component"


class Measurement(StrEnum):
    estimated = "estimated"
    actual = "actual"
    reconciled = "reconciled"


class Schema(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    usage_scope: UsageScope
    run_id: Annotated[str | None, Field(min_length=1)] = None
    turn_id: Annotated[str | None, Field(min_length=1)] = None
    operation_id: Annotated[str | None, Field(min_length=1)] = None
    component: Annotated[str | None, Field(min_length=1)] = None
    model_input_tokens: Annotated[int | None, Field(ge=0)] = None
    model_output_tokens: Annotated[int | None, Field(ge=0)] = None
    model_calls: Annotated[int | None, Field(ge=0)] = None
    tool_calls: Annotated[int | None, Field(ge=0)] = None
    repository_requests: Annotated[int | None, Field(ge=0)] = None
    elapsed_wall_time_seconds: Annotated[float | None, Field(ge=0.0)] = None
    monetary_cost_usd: Annotated[float | None, Field(ge=0.0)] = None
    command_time_seconds: Annotated[float | None, Field(ge=0.0)] = None
    command_output_size_bytes: Annotated[int | None, Field(ge=0)] = None
    artifact_size_bytes: Annotated[int | None, Field(ge=0)] = None
    repeated_token_cost_usd: Annotated[float | None, Field(ge=0.0)] = None
    measurement: Measurement | None = None
    source: Annotated[str | None, Field(min_length=1)] = None
    recorded_at: AwareDatetime


class SchemaModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    elapsed_time: Annotated[float, Field(ge=0.0)]
    files_scanned: Annotated[int, Field(ge=0)]
    candidates_returned: Annotated[int, Field(ge=0)]
    bytes_returned: Annotated[int, Field(ge=0)]
    graph_nodes_visited: Annotated[int, Field(ge=0)]
    representations_generated: Annotated[int | None, Field(ge=0)] = None
    estimated_tokens_returned: Annotated[int, Field(ge=0)]


class SchemaModel1(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    input_tokens: Annotated[
        int, Field(description="Input tokens consumed by the model invocation.", ge=0)
    ]
    output_tokens: Annotated[
        int, Field(description="Output tokens produced by the model invocation.", ge=0)
    ]
    total_tokens: Annotated[
        int,
        Field(description="Total tokens accounted for by the model invocation.", ge=0),
    ]
    cached_input_tokens: Annotated[
        int | None,
        Field(
            description="Input tokens served from a provider or adapter cache.", ge=0
        ),
    ] = None
    reasoning_tokens: Annotated[
        int | None,
        Field(
            description="Output-side reasoning tokens, when reported separately by the provider or adapter.",
            ge=0,
        ),
    ] = None
    billable_input_tokens: Annotated[
        int | None,
        Field(
            description="Input tokens counted for billing or budget accounting.", ge=0
        ),
    ] = None
    billable_output_tokens: Annotated[
        int | None,
        Field(
            description="Output tokens counted for billing or budget accounting.", ge=0
        ),
    ] = None
    estimated_cost_usd: Annotated[
        float | None,
        Field(description="Estimated provider-neutral monetary cost in USD.", ge=0.0),
    ] = None
    measurement: Annotated[
        Measurement | None,
        Field(description="Whether usage was estimated, actual, or reconciled."),
    ] = None
