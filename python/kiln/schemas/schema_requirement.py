"""
Generated Pydantic v2 models for Kiln JSON Schemas.

Do not edit this package by hand. Regenerate with:

    uv run generatemodels
"""

from __future__ import annotations

from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field


class Mode(StrEnum):
    strict = "strict"
    permissive = "permissive"


class Schema(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    schema_id: Annotated[str, Field(min_length=1)]
    instance_ref: Annotated[str, Field(min_length=1)]
    mode: Mode
