"""
Generated Pydantic v2 models for Kiln JSON Schemas.

Do not edit this package by hand. Regenerate with:

    uv run generatemodels
"""

from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, RootModel


class PinnedItemId(RootModel[str]):
    root: Annotated[str, Field(min_length=1)]


class AvailableItemId(RootModel[str]):
    root: Annotated[str, Field(min_length=1)]


class ActiveItemId(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    item_id: Annotated[str, Field(min_length=1)]
    order: Annotated[int, Field(ge=0)]


class ObservedItemId(RootModel[str]):
    root: Annotated[str, Field(min_length=1)]


class StaleItemId(RootModel[str]):
    root: Annotated[str, Field(min_length=1)]


class Schema(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    context_id: Annotated[str, Field(min_length=1)]
    pinned_item_ids: list[PinnedItemId] | None = None
    available_item_ids: list[AvailableItemId] | None = None
    active_item_ids: list[ActiveItemId] | None = None
    observed_item_ids: list[ObservedItemId] | None = None
    stale_item_ids: list[StaleItemId] | None = None
    current_token_estimate: Annotated[int, Field(ge=0)]
    model_context_limit: Annotated[int, Field(ge=0)]
    context_state_revision: Annotated[int, Field(ge=0)]
