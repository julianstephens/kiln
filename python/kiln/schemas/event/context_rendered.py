"""
Generated Pydantic v2 models for Kiln JSON Schemas.

Do not edit this package by hand. Regenerate with:

    uv run generatemodels
"""

from __future__ import annotations

from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, RootModel

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


class Schema(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    context_id: Annotated[str, Field(min_length=1)]
    render_id: Annotated[str, Field(min_length=1)]
    render_target: Annotated[
        RenderTarget,
        Field(description="Consumer or phase for which context was rendered."),
    ]
    rendered_item_count: Annotated[int, Field(ge=0)]
    rendered_item_ids: list[RenderedItemId] | None = None
    rendered_token_estimate: Annotated[int, Field(ge=0)]
    model_context_limit: Annotated[int | None, Field(ge=0)] = None
    truncated: bool | None = None
    render_artifact_reference: Annotated[
        reference.Schema | None,
        Field(description="Optional artifact reference for the rendered context."),
    ] = None
    context_state_revision: Annotated[int, Field(ge=0)]
