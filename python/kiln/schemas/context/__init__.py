"""
Generated Pydantic v2 models for Kiln JSON Schemas.

Do not edit this package by hand. Regenerate with:

    uv run generatemodels
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, RootModel

from . import action, item, plan, rendered, state


class ContextRendered(RootModel[rendered.Schema]):
    root: rendered.Schema


class ContextState(RootModel[state.Schema]):
    root: state.Schema


class ContextAction(RootModel[action.Schema]):
    root: action.Schema


class ContextPlan(RootModel[plan.Schema]):
    root: plan.Schema


class ContextItem(RootModel[item.Schema]):
    root: item.Schema


class KilnContextGeneratedPythonModelsBundle(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    context_action: ContextAction | None = None
    context_item: ContextItem | None = None
    context_plan: ContextPlan | None = None
    context_rendered: ContextRendered | None = None
    context_state: ContextState | None = None
