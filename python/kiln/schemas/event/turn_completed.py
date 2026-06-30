"""
Generated Pydantic v2 models for Kiln JSON Schemas.

Do not edit this package by hand. Regenerate with:

    uv run generatemodels
"""

from __future__ import annotations

from enum import StrEnum
from typing import Annotated

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, RootModel

from . import reference, usage


class TurnOutcome(StrEnum):
    assistant_message_produced = "assistant_message_produced"
    tool_calls_requested = "tool_calls_requested"
    tool_results_processed = "tool_results_processed"
    output_candidate_produced = "output_candidate_produced"
    validation_judgment_produced = "validation_judgment_produced"
    no_op = "no_op"


class ModelInvocationId(RootModel[str]):
    root: Annotated[str, Field(min_length=1)]


class ToolCallId(RootModel[str]):
    root: Annotated[str, Field(min_length=1)]


class Schema(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    turn_id: Annotated[
        str, Field(description="Identity for the turn that completed.", min_length=1)
    ]
    turn_index: Annotated[
        int, Field(description="Zero-based index of this turn within the run.", ge=0)
    ]
    turn_outcome: Annotated[
        TurnOutcome, Field(description="Normalized outcome of the completed turn.")
    ]
    model_invocation_ids: Annotated[
        list[ModelInvocationId] | None,
        Field(description="Model invocations performed during this turn."),
    ] = None
    tool_call_ids: Annotated[
        list[ToolCallId] | None,
        Field(description="Tool calls requested or processed during this turn."),
    ] = None
    output_reference: Annotated[
        reference.Schema | None,
        Field(
            description="Optional artifact reference for the normalized turn output."
        ),
    ] = None
    context_state_revision: Annotated[
        int | None,
        Field(description="Context state revision after the turn completed.", ge=0),
    ] = None
    budget_usage: Annotated[
        usage.Schema | None, Field(description="Budget usage committed for this turn.")
    ] = None
    completed_at: Annotated[
        AwareDatetime, Field(description="When the turn completed.")
    ]
