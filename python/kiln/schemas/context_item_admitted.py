"""
Generated Pydantic v2 models for Kiln JSON Schemas.

Do not edit this package by hand. Regenerate with:

    uv run generatemodels
"""

from __future__ import annotations

from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field


class AdmissionReason(StrEnum):
    pinned = "pinned"
    recent = "recent"
    relevant = "relevant"
    required = "required"
    dependency = "dependency"
    manual = "manual"
    plan_applied = "plan_applied"


class Schema(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    context_id: Annotated[str, Field(min_length=1)]
    item_id: Annotated[str, Field(min_length=1)]
    order: Annotated[
        int,
        Field(
            description="Position of the admitted item in active context order.", ge=0
        ),
    ]
    admission_reason: AdmissionReason
    context_plan_id: Annotated[str | None, Field(min_length=1)] = None
    estimated_tokens: Annotated[int | None, Field(ge=0)] = None
    current_token_estimate: Annotated[int | None, Field(ge=0)] = None
    context_state_revision: Annotated[int, Field(ge=0)]
