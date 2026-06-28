"""
Generated Pydantic v2 models for Kiln JSON Schemas.

Do not edit this package by hand. Regenerate with:

    uv run generatemodels
"""

from __future__ import annotations

from typing import Annotated

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, RootModel

from . import error as error_1
from . import error_category, reference, usage


class ModelInvocationId(RootModel[str]):
    root: Annotated[str, Field(min_length=1)]


class ToolCallId(RootModel[str]):
    root: Annotated[str, Field(min_length=1)]


class Schema(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    turn_id: Annotated[
        str, Field(description="Identity for the turn that failed.", min_length=1)
    ]
    turn_index: Annotated[
        int, Field(description="Zero-based index of this turn within the run.", ge=0)
    ]
    failure_category: Annotated[
        error_category.Schema, Field(description="Normalized category of turn failure.")
    ]
    error: Annotated[
        error_1.SchemaModel1,
        Field(description="Run-level error describing the turn failure."),
    ]
    partial_output_reference: Annotated[
        reference.Schema | None,
        Field(
            description="Optional artifact reference for partial turn output produced before failure."
        ),
    ] = None
    model_invocation_ids: Annotated[
        list[ModelInvocationId] | None,
        Field(description="Model invocations attempted during this turn."),
    ] = None
    tool_call_ids: Annotated[
        list[ToolCallId] | None,
        Field(description="Tool calls attempted or processed during this turn."),
    ] = None
    context_state_revision: Annotated[
        int | None,
        Field(
            description="Context state revision observed when the turn failed.", ge=0
        ),
    ] = None
    budget_usage: Annotated[
        usage.Schema | None,
        Field(description="Budget usage committed before this turn failed."),
    ] = None
    retryable: Annotated[
        bool | None, Field(description="Whether this turn failure may be retried.")
    ] = None
    failed_at: Annotated[AwareDatetime, Field(description="When the turn failed.")]
