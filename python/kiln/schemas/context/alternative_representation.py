"""
Generated Pydantic v2 models for Kiln JSON Schemas.

Do not edit this package by hand. Regenerate with:

    uv run generatemodels
"""

from __future__ import annotations

from enum import StrEnum
from typing import Annotated, Any

from pydantic import BaseModel, ConfigDict, Field


class Availability(StrEnum):
    available = "available"
    unavailable = "unavailable"


class Schema(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    representation_kind: Annotated[str, Field(min_length=1)]
    estimated_tokens: Annotated[int, Field(ge=0)]
    availability: Availability
    generation_required: bool
    quality_metadata: dict[str, Any]
