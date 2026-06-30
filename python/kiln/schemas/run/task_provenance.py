"""
Generated Pydantic v2 models for Kiln JSON Schemas.

Do not edit this package by hand. Regenerate with:

    uv run generatemodels
"""

from __future__ import annotations

from typing import Annotated

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field


class Schema(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    source_kind: Annotated[str, Field(min_length=1)]
    source_id: Annotated[str, Field(min_length=1)]
    trusted: bool
    created_at: AwareDatetime
