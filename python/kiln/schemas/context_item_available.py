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


class ItemKind(StrEnum):
    system_instruction = "system_instruction"
    user_message = "user_message"
    assistant_message = "assistant_message"
    tool_result = "tool_result"
    repository_source = "repository_source"
    repository_search_result = "repository_search_result"
    artifact = "artifact"
    summary = "summary"
    memory = "memory"
    validation_result = "validation_result"
    diagnostic = "diagnostic"


class AvailabilityReason(StrEnum):
    observed = "observed"
    retrieved = "retrieved"
    generated = "generated"
    pinned = "pinned"
    restored = "restored"
    manual = "manual"


class Priority(StrEnum):
    low = "low"
    normal = "normal"
    high = "high"
    required = "required"


class Schema(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    context_id: Annotated[str, Field(min_length=1)]
    item_id: Annotated[str, Field(min_length=1)]
    item_kind: ItemKind
    availability_reason: AvailabilityReason
    source_reference: Annotated[
        reference.Schema | None,
        Field(
            description="Artifact, repository, or external reference for the item source."
        ),
    ] = None
    estimated_tokens: Annotated[int, Field(ge=0)]
    priority: Priority | None = None
    pinned: bool | None = None
    metadata: Annotated[
        dict[str, str | float | int | bool] | None,
        Field(description="Small non-sensitive item metadata."),
    ] = None
