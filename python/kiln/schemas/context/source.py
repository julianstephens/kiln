"""
Generated Pydantic v2 models for Kiln JSON Schemas.

Do not edit this package by hand. Regenerate with:

    uv run generatemodels
"""

from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

from . import byte_range, source_range


class Schema(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    repository_path: Annotated[str, Field(min_length=1)]
    source_digest: Annotated[str, Field(min_length=1)]
    line_ranges: list[source_range.Schema]
    byte_ranges: list[byte_range.Schema]
    qualified_name: Annotated[str | None, Field(min_length=1)] = None
    language: Annotated[str | None, Field(min_length=1)] = None
