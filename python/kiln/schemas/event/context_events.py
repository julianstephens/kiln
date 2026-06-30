"""
Generated Pydantic v2 models for Kiln JSON Schemas.

Do not edit this package by hand. Regenerate with:

    uv run generatemodels
"""

from __future__ import annotations

from enum import StrEnum


class Schema(StrEnum):
    context_plan_requested = "context.plan_requested"
    context_plan_produced = "context.plan_produced"
    context_plan_applied = "context.plan_applied"
    context_item_available = "context.item_available"
    context_item_admitted = "context.item_admitted"
    context_item_evicted = "context.item_evicted"
    context_rendered = "context.rendered"
