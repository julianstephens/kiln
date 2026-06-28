"""
Generated Pydantic v2 models for Kiln JSON Schemas.

Do not edit this package by hand. Regenerate with:

    uv run generatemodels
"""

from __future__ import annotations

from enum import StrEnum


class Schema(StrEnum):
    budget_initialized = "budget.initialized"
    budget_reserved = "budget.reserved"
    budget_committed = "budget.committed"
    budget_denied = "budget.denied"
    budget_exhausted = "budget.exhausted"
    budget_reconciled = "budget.reconciled"
