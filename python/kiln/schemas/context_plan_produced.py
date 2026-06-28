"""
Generated Pydantic v2 models for Kiln JSON Schemas.

Do not edit this package by hand. Regenerate with:

    uv run generatemodels
"""

from __future__ import annotations

from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

from . import reference


class PlanningStrategy(StrEnum):
    recency = "recency"
    relevance = "relevance"
    pinned_first = "pinned_first"
    budget_fit = "budget_fit"
    hybrid = "hybrid"
    manual = "manual"


class AdmissionReason(StrEnum):
    pinned = "pinned"
    recent = "recent"
    relevant = "relevant"
    required = "required"
    dependency = "dependency"
    manual = "manual"


class PlannedActiveItem(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    item_id: Annotated[str, Field(min_length=1)]
    order: Annotated[int, Field(ge=0)]
    estimated_tokens: Annotated[int | None, Field(ge=0)] = None
    admission_reason: AdmissionReason


class EvictionReason(StrEnum):
    token_budget = "token_budget"
    stale = "stale"
    superseded = "superseded"
    low_relevance = "low_relevance"
    manual = "manual"


class PlannedEviction(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    item_id: Annotated[str, Field(min_length=1)]
    eviction_reason: EvictionReason


class Schema(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    context_id: Annotated[str, Field(min_length=1)]
    context_plan_request_id: Annotated[str, Field(min_length=1)]
    context_plan_id: Annotated[str, Field(min_length=1)]
    planning_strategy: PlanningStrategy | None = None
    planned_active_items: Annotated[
        list[PlannedActiveItem],
        Field(
            description="Items selected by the produced context plan, in intended render order.",
            min_length=1,
        ),
    ]
    planned_evictions: list[PlannedEviction] | None = None
    estimated_token_count: Annotated[int, Field(ge=0)]
    model_context_limit: Annotated[int | None, Field(ge=0)] = None
    plan_artifact_reference: reference.Schema | None = None
