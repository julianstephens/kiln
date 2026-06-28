"""
Generated Pydantic v2 models for Kiln JSON Schemas.

Do not edit this package by hand. Regenerate with:

    uv run generatemodels
"""

from __future__ import annotations

from enum import StrEnum
from typing import Annotated

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field

from . import reference


class TurnKind(StrEnum):
    initial = "initial"
    user_followup = "user_followup"
    tool_followup = "tool_followup"
    recovery = "recovery"
    validation = "validation"
    output_production = "output_production"


class Schema(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    turn_id: Annotated[
        str, Field(description="Identity for the turn that started.", min_length=1)
    ]
    turn_index: Annotated[
        int, Field(description="Zero-based index of this turn within the run.", ge=0)
    ]
    turn_kind: Annotated[TurnKind, Field(description="Kind of turn being started.")]
    parent_turn_id: Annotated[
        str | None,
        Field(
            description="Parent turn that caused this turn, when applicable.",
            min_length=1,
        ),
    ] = None
    input_reference: Annotated[
        reference.Schema | None,
        Field(description="Optional artifact reference for the turn input."),
    ] = None
    context_id: Annotated[
        str, Field(description="Context ledger used by this turn.", min_length=1)
    ]
    context_state_revision: Annotated[
        int | None,
        Field(description="Context state revision observed at turn start.", ge=0),
    ] = None
    budget_id: Annotated[
        str | None,
        Field(
            description="Budget ledger used by this turn, when applicable.",
            min_length=1,
        ),
    ] = None
    started_at: Annotated[AwareDatetime, Field(description="When the turn started.")]
