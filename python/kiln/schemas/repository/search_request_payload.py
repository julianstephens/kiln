"""
Generated Pydantic v2 models for Kiln JSON Schemas.

Do not edit this package by hand. Regenerate with:

    uv run generatemodels
"""

from __future__ import annotations

from enum import StrEnum
from typing import Annotated, Any

from pydantic import BaseModel, ConfigDict, Field


class Mode(StrEnum):
    lexical = "lexical"
    full_text = "full-text"
    symbol_name = "symbol-name"
    qualified_name = "qualified-name"
    semantic = "semantic"
    hybrid = "hybrid"


class Schema(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    query: Annotated[str, Field(min_length=1)]
    mode: Mode
    limit: Annotated[int, Field(ge=1)]
    filters: list[dict[str, Any]] | None = None
    representation_preference: Annotated[str | None, Field(min_length=1)] = None
    minimum_score: Annotated[float | None, Field(ge=0.0)] = None
    result_size_limit: Annotated[int | None, Field(ge=1)] = None
