"""
Generated Pydantic v2 models for Kiln JSON Schemas.

Do not edit this package by hand. Regenerate with:

    uv run generatemodels
"""

from __future__ import annotations

from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, RootModel


class PolicyKind(StrEnum):
    security = "security"
    privacy = "privacy"
    compliance = "compliance"


class Input(RootModel[str]):
    root: Annotated[str, Field(min_length=1)]


class Schema(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    policy_id: Annotated[str, Field(min_length=1)]
    policy_kind: PolicyKind
    inputs: Annotated[list[Input], Field(min_length=1)]
    failure_code: Annotated[str, Field(min_length=1)]
