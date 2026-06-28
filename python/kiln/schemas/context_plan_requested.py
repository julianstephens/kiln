"""
Generated Pydantic v2 models for Kiln JSON Schemas.

Do not edit this package by hand. Regenerate with:

    uv run generatemodels
"""

from __future__ import annotations

from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, RootModel


class PlanningGoal(StrEnum):
    initial_context = "initial_context"
    turn_context = "turn_context"
    tool_context = "tool_context"
    output_production = "output_production"
    validation = "validation"
    recovery = "recovery"


class PinnedItemId(RootModel[str]):
    root: Annotated[str, Field(min_length=1)]


class MustIncludeItemId(RootModel[str]):
    root: Annotated[str, Field(min_length=1)]


class MustExcludeItemId(RootModel[str]):
    root: Annotated[str, Field(min_length=1)]


class Constraints(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    target_token_budget: Annotated[int | None, Field(ge=0)] = None
    must_include_item_ids: list[MustIncludeItemId] | None = None
    must_exclude_item_ids: list[MustExcludeItemId] | None = None
    allow_compression: bool | None = None
    allow_eviction: bool | None = None


class Schema(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    context_id: Annotated[str, Field(min_length=1)]
    context_plan_request_id: Annotated[
        str,
        Field(
            description="Operation-local identity for this context planning request.",
            min_length=1,
        ),
    ]
    planning_goal: Annotated[
        PlanningGoal, Field(description="Reason a context plan was requested.")
    ]
    model_context_limit: Annotated[int, Field(ge=0)]
    current_token_estimate: Annotated[int, Field(ge=0)]
    available_item_count: Annotated[int | None, Field(ge=0)] = None
    active_item_count: Annotated[int | None, Field(ge=0)] = None
    pinned_item_ids: list[PinnedItemId] | None = None
    constraints: Annotated[
        Constraints | None,
        Field(description="Planning constraints supplied to the context planner."),
    ] = None
