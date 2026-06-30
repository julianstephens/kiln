"""
Generated Pydantic v2 models for Kiln JSON Schemas.

Do not edit this package by hand. Regenerate with:

    uv run generatemodels
"""

from __future__ import annotations

from enum import StrEnum
from typing import Annotated

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, RootModel

from . import reference


class RenderTarget(StrEnum):
    model_invocation = "model_invocation"
    tool_invocation = "tool_invocation"
    output_production = "output_production"
    validation = "validation"
    diagnostic = "diagnostic"
    preview = "preview"


class RenderedItemId(RootModel[str]):
    root: Annotated[str, Field(min_length=1)]


class RenderRole(StrEnum):
    system = "system"
    developer = "developer"
    user = "user"
    assistant = "assistant"
    tool = "tool"
    context = "context"
    metadata = "metadata"


class RenderedItem(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    item_id: Annotated[str, Field(min_length=1)]
    order: Annotated[int, Field(ge=0)]
    estimated_tokens: Annotated[int | None, Field(ge=0)] = None
    render_role: RenderRole | None = None


class TruncationReason(StrEnum):
    model_context_limit = "model_context_limit"
    target_token_budget = "target_token_budget"
    item_size_limit = "item_size_limit"
    policy = "policy"
    manual = "manual"


class Schema(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    render_id: Annotated[
        str,
        Field(
            description="Stable identity for this rendered context instance.",
            min_length=1,
        ),
    ]
    context_id: Annotated[
        str, Field(description="Context ledger rendered from.", min_length=1)
    ]
    context_plan_id: Annotated[
        str | None,
        Field(
            description="Context plan used to produce this render, when applicable.",
            min_length=1,
        ),
    ] = None
    render_target: Annotated[
        RenderTarget,
        Field(description="Consumer or phase this context render was produced for."),
    ]
    target_operation_id: Annotated[
        str | None,
        Field(
            description="Operation that consumed or requested this rendered context.",
            min_length=1,
        ),
    ] = None
    context_state_revision: Annotated[
        int, Field(description="Context state revision rendered from.", ge=0)
    ]
    rendered_item_ids: Annotated[
        list[RenderedItemId],
        Field(description="Context items included in this render."),
    ]
    rendered_items: Annotated[
        list[RenderedItem] | None,
        Field(
            description="Context items included in this render with render order and token estimates."
        ),
    ] = None
    rendered_item_count: Annotated[
        int, Field(description="Number of context items included in this render.", ge=0)
    ]
    rendered_token_estimate: Annotated[
        int, Field(description="Estimated token count for the rendered context.", ge=0)
    ]
    model_context_limit: Annotated[
        int | None,
        Field(
            description="Model context limit used when rendering, when applicable.",
            ge=1,
        ),
    ] = None
    truncated: Annotated[
        bool | None, Field(description="Whether rendered context was truncated.")
    ] = None
    truncation_reason: Annotated[
        TruncationReason | None,
        Field(description="Reason rendered context was truncated."),
    ] = None
    render_artifact_reference: Annotated[
        reference.Schema | None,
        Field(
            description="Artifact reference for rendered context content, when stored durably."
        ),
    ] = None
    content_hash: Annotated[
        str | None,
        Field(
            description="Content hash for the rendered context payload, when not stored as an artifact.",
            min_length=1,
        ),
    ] = None
    rendered_at: Annotated[
        AwareDatetime, Field(description="When this context render was produced.")
    ]
