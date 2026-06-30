"""
Generated Pydantic v2 models for Kiln JSON Schemas.

Do not edit this package by hand. Regenerate with:

    uv run generatemodels
"""

from __future__ import annotations

from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, RootModel


class AllowedSourceKind(RootModel[str]):
    root: Annotated[str, Field(min_length=1)]


class MinimumSupportLevel(StrEnum):
    direct = "direct"
    indirect = "indirect"


class Schema(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    citation_model: Annotated[str, Field(min_length=1)]
    allowed_source_kinds: Annotated[list[AllowedSourceKind], Field(min_length=1)]
    minimum_support_level: MinimumSupportLevel
