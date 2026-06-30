"""
Generated Pydantic v2 models for Kiln JSON Schemas.

Do not edit this package by hand. Regenerate with:

    uv run generatemodels
"""

from __future__ import annotations

from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field


class ApprovalKind(StrEnum):
    human = "human"
    automated = "automated"


class Schema(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    approval_kind: ApprovalKind
    approver_role: Annotated[str, Field(min_length=1)]
    reason: Annotated[str, Field(min_length=1)]
