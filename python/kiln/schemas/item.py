"""
Generated Pydantic v2 models for Kiln JSON Schemas.

Do not edit this package by hand. Regenerate with:

    uv run generatemodels
"""

from __future__ import annotations

from enum import StrEnum
from typing import Annotated

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field

from . import candidate, reference, source


class ItemKind(StrEnum):
    system_instruction = "system_instruction"
    developer_instruction = "developer_instruction"
    user_message = "user_message"
    assistant_message = "assistant_message"
    tool_request = "tool_request"
    tool_result = "tool_result"
    repository_source = "repository_source"
    repository_search_result = "repository_search_result"
    artifact = "artifact"
    summary = "summary"
    memory = "memory"
    validation_result = "validation_result"
    diagnostic = "diagnostic"
    run_state = "run_state"
    other = "other"


class ItemStatus(StrEnum):
    available = "available"
    active = "active"
    evicted = "evicted"
    stale = "stale"
    invalidated = "invalidated"


class ReferenceKind(StrEnum):
    inline = "inline"
    artifact = "artifact"
    repository_source = "repository_source"
    repository_candidate = "repository_candidate"
    message = "message"
    state = "state"
    external = "external"


class Priority(StrEnum):
    low = "low"
    normal = "normal"
    high = "high"
    required = "required"


class AdmissionReason(StrEnum):
    pinned = "pinned"
    recent = "recent"
    relevant = "relevant"
    required = "required"
    dependency = "dependency"
    manual = "manual"
    plan_applied = "plan_applied"


class EvictionReason(StrEnum):
    token_budget = "token_budget"
    stale = "stale"
    superseded = "superseded"
    low_relevance = "low_relevance"
    manual = "manual"
    plan_applied = "plan_applied"
    context_reset = "context_reset"


class ContentReference(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    reference_kind: Annotated[
        ReferenceKind, Field(description="Kind of content reference used by the item.")
    ]
    inline_content: Annotated[
        str | None,
        Field(description="Inline context content for small items.", min_length=1),
    ] = None
    artifact_reference: Annotated[
        reference.Schema | None,
        Field(description="Artifact containing the item content."),
    ] = None
    repository_source: Annotated[
        source.Schema | None,
        Field(description="Repository source location represented by this item."),
    ] = None
    repository_candidate: Annotated[
        candidate.Schema | None,
        Field(description="Repository candidate represented by this item."),
    ] = None
    message_id: Annotated[
        str | None,
        Field(description="Message identity represented by this item.", min_length=1),
    ] = None
    state_reference: Annotated[
        str | None,
        Field(
            description="Opaque state reference represented by this item.", min_length=1
        ),
    ] = None
    external_reference: Annotated[
        str | None,
        Field(description="External reference represented by this item.", min_length=1),
    ] = None


class Schema(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    item_id: Annotated[
        str, Field(description="Stable identity for this context item.", min_length=1)
    ]
    context_id: Annotated[
        str, Field(description="Context ledger this item belongs to.", min_length=1)
    ]
    item_kind: Annotated[
        ItemKind, Field(description="Kind of content represented by this context item.")
    ]
    item_status: Annotated[
        ItemStatus, Field(description="Current lifecycle status of the context item.")
    ]
    content_reference: Annotated[
        ContentReference,
        Field(description="Reference to the item's underlying content."),
    ]
    estimated_tokens: Annotated[
        int,
        Field(
            description="Estimated token cost of admitting this item into context.",
            ge=0,
        ),
    ]
    priority: Annotated[
        Priority | None,
        Field(description="Planner-visible priority for this context item."),
    ] = None
    pinned: Annotated[
        bool | None,
        Field(
            description="Whether this item should be treated as pinned by context planning."
        ),
    ] = None
    source_event_id: Annotated[
        str | None,
        Field(
            description="Event that made this item available, when applicable.",
            min_length=1,
        ),
    ] = None
    source_operation_id: Annotated[
        str | None,
        Field(
            description="Operation that produced or retrieved this item, when applicable.",
            min_length=1,
        ),
    ] = None
    active_order: Annotated[
        int | None,
        Field(
            description="Order of this item when admitted into active context.", ge=0
        ),
    ] = None
    admission_reason: Annotated[
        AdmissionReason | None,
        Field(description="Reason this item was admitted into active context."),
    ] = None
    eviction_reason: Annotated[
        EvictionReason | None,
        Field(description="Reason this item was evicted from active context."),
    ] = None
    created_at: Annotated[
        AwareDatetime, Field(description="When this context item was created.")
    ]
    admitted_at: Annotated[
        AwareDatetime | None,
        Field(description="When this item was admitted into active context."),
    ] = None
    evicted_at: Annotated[
        AwareDatetime | None,
        Field(description="When this item was evicted from active context."),
    ] = None
    stale_at: Annotated[
        AwareDatetime | None, Field(description="When this item became stale.")
    ] = None
    invalidated_at: Annotated[
        AwareDatetime | None, Field(description="When this item was invalidated.")
    ] = None
    metadata: Annotated[
        dict[str, str | float | int | bool] | None,
        Field(description="Small non-sensitive item metadata."),
    ] = None
