"""
Generated Pydantic v2 models for Kiln JSON Schemas.

Do not edit this package by hand. Regenerate with:

    uv run generatemodels
"""

from __future__ import annotations

from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field


class EvictionReason(StrEnum):
    token_budget = "token_budget"
    stale = "stale"
    superseded = "superseded"
    low_relevance = "low_relevance"
    manual = "manual"
    plan_applied = "plan_applied"
    context_reset = "context_reset"


class Schema(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    context_id: Annotated[str, Field(min_length=1)]
    item_id: Annotated[str, Field(min_length=1)]
    eviction_reason: EvictionReason
    context_plan_id: Annotated[str | None, Field(min_length=1)] = None
    previous_order: Annotated[int | None, Field(ge=0)] = None
    estimated_tokens_freed: Annotated[int | None, Field(ge=0)] = None
    current_token_estimate: Annotated[int | None, Field(ge=0)] = None
    context_state_revision: Annotated[int, Field(ge=0)]
