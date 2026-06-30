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


class ActionKind(StrEnum):
    make_available = "make_available"
    admit = "admit"
    evict = "evict"
    pin = "pin"
    unpin = "unpin"
    mark_stale = "mark_stale"
    invalidate = "invalidate"
    compress = "compress"
    reorder = "reorder"


class Reason(StrEnum):
    pinned = "pinned"
    recent = "recent"
    relevant = "relevant"
    required = "required"
    dependency = "dependency"
    token_budget = "token_budget"
    stale = "stale"
    superseded = "superseded"
    low_relevance = "low_relevance"
    manual = "manual"
    plan_applied = "plan_applied"
    context_reset = "context_reset"
    compression_budget = "compression_budget"
    invalid_source = "invalid_source"


class Schema(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    action_id: Annotated[
        str, Field(description="Stable identity for this context action.", min_length=1)
    ]
    context_id: Annotated[
        str, Field(description="Context ledger this action applies to.", min_length=1)
    ]
    context_plan_id: Annotated[
        str | None,
        Field(
            description="Context plan that produced this action, when applicable.",
            min_length=1,
        ),
    ] = None
    item_id: Annotated[
        str, Field(description="Context item affected by this action.", min_length=1)
    ]
    action_kind: Annotated[ActionKind, Field(description="Kind of context mutation.")]
    reason: Annotated[
        Reason | None, Field(description="Planner-visible reason for the action.")
    ] = None
    order: Annotated[
        int | None,
        Field(
            description="Active context order after this action, when applicable.", ge=0
        ),
    ] = None
    previous_order: Annotated[
        int | None,
        Field(
            description="Previous active context order before this action, when applicable.",
            ge=0,
        ),
    ] = None
    estimated_tokens_before: Annotated[
        int | None,
        Field(
            description="Estimated token count for this item before the action.", ge=0
        ),
    ] = None
    estimated_tokens_after: Annotated[
        int | None,
        Field(
            description="Estimated token count for this item after the action.", ge=0
        ),
    ] = None
    replacement_item_id: Annotated[
        str | None,
        Field(
            description="Replacement context item produced by this action, when applicable.",
            min_length=1,
        ),
    ] = None
    artifact_reference: Annotated[
        reference.Schema | None,
        Field(
            description="Artifact created or consumed by this action, when applicable."
        ),
    ] = None
