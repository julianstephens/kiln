"""
Generated Pydantic v2 models for Kiln JSON Schemas.

Do not edit this package by hand. Regenerate with:

    uv run generatemodels
"""

from __future__ import annotations

from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field


class Measurement(StrEnum):
    estimated = "estimated"
    actual = "actual"
    reconciled = "reconciled"


class Schema(BaseModel):
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
