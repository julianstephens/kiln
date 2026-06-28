"""
Generated Pydantic v2 models for Kiln JSON Schemas.

Do not edit this package by hand. Regenerate with:

    uv run generatemodels
"""

from __future__ import annotations

from enum import StrEnum
from typing import Annotated

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field

from . import limits, usage


class ReservationScope(StrEnum):
    run = "run"
    turn = "turn"
    operation = "operation"
    component = "component"


class ReservationStatus(StrEnum):
    active = "active"
    partially_committed = "partially_committed"
    committed = "committed"
    released = "released"
    expired = "expired"
    canceled = "canceled"


class ReservationReason(StrEnum):
    model_invocation = "model_invocation"
    tool_invocation = "tool_invocation"
    repository_operation = "repository_operation"
    output_production = "output_production"
    validation = "validation"
    artifact_write = "artifact_write"
    runtime_operation = "runtime_operation"
    other = "other"


class Schema(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    reservation_id: Annotated[
        str,
        Field(description="Stable identity for this budget reservation.", min_length=1),
    ]
    budget_id: Annotated[
        str,
        Field(
            description="Budget ledger or accounting scope this reservation belongs to.",
            min_length=1,
        ),
    ]
    reservation_scope: Annotated[
        ReservationScope,
        Field(description="Scope for which budget capacity was reserved."),
    ]
    run_id: Annotated[
        str | None,
        Field(
            description="Run associated with this reservation, when applicable.",
            min_length=1,
        ),
    ] = None
    turn_id: Annotated[
        str | None,
        Field(
            description="Turn associated with this reservation, when applicable.",
            min_length=1,
        ),
    ] = None
    operation_id: Annotated[
        str | None,
        Field(
            description="Operation associated with this reservation, when applicable.",
            min_length=1,
        ),
    ] = None
    component: Annotated[
        str | None,
        Field(
            description="Logical component associated with this reservation, when applicable.",
            min_length=1,
        ),
    ] = None
    reserved_amounts: Annotated[
        limits.Schema, Field(description="Budget amounts reserved by dimension.")
    ]
    committed_usage: Annotated[
        usage.Schema | None,
        Field(description="Usage already committed against this reservation."),
    ] = None
    reservation_status: Annotated[
        ReservationStatus, Field(description="Current status of the reservation.")
    ]
    reservation_reason: Annotated[
        ReservationReason | None,
        Field(description="Reason the reservation was created."),
    ] = None
    created_at: Annotated[
        AwareDatetime, Field(description="When the reservation was created.")
    ]
    expires_at: Annotated[
        AwareDatetime | None,
        Field(description="When the reservation expires if not committed or released."),
    ] = None
    closed_at: Annotated[
        AwareDatetime | None,
        Field(description="When the reservation reached a terminal status."),
    ] = None
