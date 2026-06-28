"""
Generated Pydantic v2 models for Kiln JSON Schemas.

Do not edit this package by hand. Regenerate with:

    uv run generatemodels
"""

from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

from . import candidate


class Schema(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    candidates: list[candidate.Schema]
    result_count: Annotated[int, Field(ge=0)]
    truncated: bool
