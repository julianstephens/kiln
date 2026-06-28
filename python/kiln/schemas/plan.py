"""
Generated Pydantic v2 models for Kiln JSON Schemas.

Do not edit this package by hand. Regenerate with:

    uv run generatemodels
"""

from __future__ import annotations

from enum import StrEnum
from typing import Annotated

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field

from . import action, reference


class PlanningGoal(StrEnum):
    initial_context = "initial_context"
    turn_context = "turn_context"
    tool_context = "tool_context"
    model_invocation = "model_invocation"
    output_production = "output_production"
    validation = "validation"
    recovery = "recovery"


class PlanningStatus(StrEnum):
    produced = "produced"
    applied = "applied"
    rejected = "rejected"
    superseded = "superseded"
    failed = "failed"


class PlanningStrategy(StrEnum):
    recency = "recency"
    relevance = "relevance"
    pinned_first = "pinned_first"
    budget_fit = "budget_fit"
    hybrid = "hybrid"
    manual = "manual"


class PlannedActiveItem(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    item_id: Annotated[str, Field(min_length=1)]
    order: Annotated[int, Field(ge=0)]
    estimated_tokens: Annotated[int | None, Field(ge=0)] = None


class Schema(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    context_plan_id: Annotated[
        str, Field(description="Stable identity for this context plan.", min_length=1)
    ]
    context_plan_request_id: Annotated[
        str | None,
        Field(
            description="Request identity that caused this plan to be produced.",
            min_length=1,
        ),
    ] = None
    context_id: Annotated[
        str, Field(description="Context ledger this plan applies to.", min_length=1)
    ]
    planning_goal: Annotated[
        PlanningGoal, Field(description="Reason this context plan was produced.")
    ]
    planning_status: Annotated[
        PlanningStatus, Field(description="Current status of the context plan.")
    ]
    planning_strategy: Annotated[
        PlanningStrategy | None,
        Field(description="Strategy used to produce this context plan."),
    ] = None
    planned_actions: Annotated[
        list[action.Schema],
        Field(description="Context mutations proposed by this plan.", min_length=1),
    ]
    planned_active_items: Annotated[
        list[PlannedActiveItem] | None,
        Field(
            description="Planned active context items in render order after applying the plan."
        ),
    ] = None
    estimated_token_count: Annotated[
        int,
        Field(
            description="Estimated active-context token count after applying the plan.",
            ge=0,
        ),
    ]
    model_context_limit: Annotated[
        int, Field(description="Model context limit used during planning.", ge=1)
    ]
    target_token_budget: Annotated[
        int | None,
        Field(
            description="Planner target budget, when lower than the full model context limit.",
            ge=0,
        ),
    ] = None
    source_context_state_revision: Annotated[
        int | None,
        Field(description="Context state revision used as input to this plan.", ge=0),
    ] = None
    result_context_state_revision: Annotated[
        int | None,
        Field(
            description="Context state revision after the plan was applied, when applicable.",
            ge=0,
        ),
    ] = None
    plan_artifact_reference: Annotated[
        reference.Schema | None,
        Field(
            description="Artifact reference for this context plan, when stored durably outside the event stream."
        ),
    ] = None
    created_at: Annotated[
        AwareDatetime, Field(description="When the context plan was created.")
    ]
    applied_at: Annotated[
        AwareDatetime | None, Field(description="When the context plan was applied.")
    ] = None
    closed_at: Annotated[
        AwareDatetime | None,
        Field(
            description="When the context plan reached a terminal non-applied status."
        ),
    ] = None
