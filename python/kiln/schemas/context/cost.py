"""
Generated Pydantic v2 models for Kiln JSON Schemas.

Do not edit this package by hand. Regenerate with:

    uv run generatemodels
"""

from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field


class Schema(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    estimated_tokens: Annotated[int, Field(ge=0)]
    estimated_bytes: Annotated[int, Field(ge=0)]
    estimation_method: Annotated[str, Field(min_length=1)]
    tokenizer_family: Annotated[str | None, Field(min_length=1)] = None
    estimated_confidence: Annotated[int | None, Field(ge=0)] = None
