"""
Generated Pydantic v2 models for Kiln JSON Schemas.

Do not edit this package by hand. Regenerate with:

    uv run generatemodels
"""

from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

from . import source_range as source_range_1


class Schema(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    target_source: Annotated[str, Field(min_length=1)]
    qualified_name: Annotated[str | None, Field(min_length=1)] = None
    source_range: source_range_1.Schema | None = None
    representation_preference: Annotated[str, Field(min_length=1)]
    max_result_size: Annotated[int, Field(ge=1)]
