"""
Generated Pydantic v2 models for Kiln JSON Schemas.

Do not edit this package by hand. Regenerate with:

    uv run generatemodels
"""

from __future__ import annotations

from enum import StrEnum
from typing import Annotated, Any

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, RootModel

from . import limits, reservation, usage


class BudgetDetails(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    configured_limit: Annotated[int, Field(ge=0)]
    reserved_amount: Annotated[int, Field(ge=0)]
    committed_amount: Annotated[int, Field(ge=0)]
    remaining_amount: Annotated[int, Field(ge=0)]
    exhausted: bool


class BudgetLimits(RootModel[limits.Schema]):
    root: limits.Schema


class BudgetUsage(RootModel[usage.Schema]):
    root: usage.Schema


class BudgetReservation(RootModel[reservation.Schema]):
    root: reservation.Schema


class KilnBudgetGeneratedPythonModelsBundle(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    budget_exhaustion: BudgetExhaustion | None = None
    budget_limits: BudgetLimits | None = None
    budget_reservation: BudgetReservation | None = None
    budget_state: BudgetState | None = None
    budget_usage: BudgetUsage | None = None


class ExhaustionScope(StrEnum):
    run = "run"
    turn = "turn"
    operation = "operation"
    component = "component"


class ExhaustedDimension(StrEnum):
    model_input_tokens = "model_input_tokens"
    model_output_tokens = "model_output_tokens"
    model_calls = "model_calls"
    tool_calls = "tool_calls"
    repository_requests = "repository_requests"
    elapsed_wall_time_seconds = "elapsed_wall_time_seconds"
    monetary_cost_usd = "monetary_cost_usd"
    command_time_seconds = "command_time_seconds"
    command_output_size_bytes = "command_output_size_bytes"
    artifact_size_bytes = "artifact_size_bytes"
    repeated_token_cost_usd = "repeated_token_cost_usd"


class ExhaustionReason(StrEnum):
    reservation_exceeds_remaining = "reservation_exceeds_remaining"
    committed_usage_reached_limit = "committed_usage_reached_limit"
    reconciliation_reached_limit = "reconciliation_reached_limit"
    external_limit_reached = "external_limit_reached"
    time_limit_reached = "time_limit_reached"
    cost_limit_reached = "cost_limit_reached"
    unknown = "unknown"


class Schema(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    exhaustion_id: Annotated[
        str,
        Field(
            description="Stable identity for this budget exhaustion record.",
            min_length=1,
        ),
    ]
    budget_id: Annotated[
        str,
        Field(
            description="Budget ledger or accounting scope that became exhausted.",
            min_length=1,
        ),
    ]
    exhaustion_scope: Annotated[
        ExhaustionScope, Field(description="Scope in which budget exhaustion occurred.")
    ]
    run_id: Annotated[
        str | None,
        Field(
            description="Run associated with this exhaustion record, when applicable.",
            min_length=1,
        ),
    ] = None
    turn_id: Annotated[
        str | None,
        Field(
            description="Turn associated with this exhaustion record, when applicable.",
            min_length=1,
        ),
    ] = None
    operation_id: Annotated[
        str | None,
        Field(
            description="Operation associated with this exhaustion record, when applicable.",
            min_length=1,
        ),
    ] = None
    component: Annotated[
        str | None,
        Field(
            description="Logical component associated with this exhaustion record, when applicable.",
            min_length=1,
        ),
    ] = None
    triggering_reservation_id: Annotated[
        str | None,
        Field(
            description="Reservation that caused or revealed exhaustion, when applicable.",
            min_length=1,
        ),
    ] = None
    triggering_commitment_id: Annotated[
        str | None,
        Field(
            description="Committed usage transaction that caused or revealed exhaustion, when applicable.",
            min_length=1,
        ),
    ] = None
    triggering_reconciliation_id: Annotated[
        str | None,
        Field(
            description="Reconciliation operation that caused or revealed exhaustion, when applicable.",
            min_length=1,
        ),
    ] = None
    requested_amounts: Annotated[
        limits.Schema | None,
        Field(
            description="Budget amounts requested when exhaustion was detected, when applicable."
        ),
    ] = None
    committed_usage: Annotated[
        usage.Schema | None,
        Field(
            description="Usage committed when exhaustion was detected, when applicable."
        ),
    ] = None
    exhausted_dimensions: Annotated[
        list[ExhaustedDimension],
        Field(description="Budget dimensions that were exhausted.", min_length=1),
    ]
    exhaustion_reason: Annotated[
        ExhaustionReason, Field(description="Reason budget exhaustion was detected.")
    ]
    state_at_exhaustion: Annotated[
        Schema_1, Field(description="Budget state when exhaustion was detected.")
    ]
    exhausted_at: Annotated[
        AwareDatetime, Field(description="When budget exhaustion was detected.")
    ]


class BudgetExhaustion(RootModel[Schema]):
    root: Schema


class Mode(StrEnum):
    installation_default = "installation_default"
    unlimited = "unlimited"
    custom = "custom"


class Schema_1(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    state_revision: Annotated[int, Field(ge=0)]
    latest_transaction_sequence: Annotated[int, Field(ge=0)]
    estimate_vs_actuals: dict[str, Any]
    mode: Mode
    model_input_tokens: BudgetDetails | None = None
    model_output_tokens: BudgetDetails | None = None
    model_calls: BudgetDetails | None = None
    tool_calls: BudgetDetails | None = None
    repository_requests: BudgetDetails | None = None
    elapsed_wall_time_seconds: BudgetDetails | None = None
    monetary_cost_usd: BudgetDetails | None = None
    command_time_seconds: BudgetDetails | None = None
    command_output_size_bytes: BudgetDetails | None = None
    artifact_size_bytes: BudgetDetails | None = None
    repeated_token_cost_usd: BudgetDetails | None = None


class BudgetState(RootModel[Schema_1]):
    root: Schema_1
