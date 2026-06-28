"""
Generated Pydantic v2 models for Kiln JSON Schemas.

Do not edit this package by hand. Regenerate with:

    uv run generatemodels
"""

from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, RootModel


class ActiveItem(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    item_id: Annotated[str, Field(min_length=1)]
    order: Annotated[int, Field(ge=0)]
    estimated_tokens: Annotated[int | None, Field(ge=0)] = None


class AdmittedItemId(RootModel[str]):
    root: Annotated[str, Field(min_length=1)]


class EvictedItemId(RootModel[str]):
    root: Annotated[str, Field(min_length=1)]


class Schema(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    context_id: Annotated[str, Field(min_length=1)]
    context_plan_id: Annotated[str, Field(min_length=1)]
    context_state_revision: Annotated[int, Field(ge=0)]
    active_items: Annotated[
        list[ActiveItem],
        Field(description="Active context items after applying the plan."),
    ]
    admitted_item_ids: list[AdmittedItemId] | None = None
    evicted_item_ids: list[EvictedItemId] | None = None
    current_token_estimate: Annotated[int, Field(ge=0)]
    model_context_limit: Annotated[int, Field(ge=0)]
