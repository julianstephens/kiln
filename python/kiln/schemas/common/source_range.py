"""
Generated Pydantic v2 models for Kiln JSON Schemas.

Do not edit this package by hand. Regenerate with:

    uv run generatemodels
"""

from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field


class Start(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    line: Annotated[int, Field(ge=1)]
    column: Annotated[int, Field(ge=1)]


class End(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    line: Annotated[int, Field(ge=1)]
    column: Annotated[int, Field(ge=1)]


class Schema(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    start: Start
    end: End
