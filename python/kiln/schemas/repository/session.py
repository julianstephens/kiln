"""
Generated Pydantic v2 models for Kiln JSON Schemas.

Do not edit this package by hand. Regenerate with:

    uv run generatemodels
"""

from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, RootModel

from . import identifier


class Capability(RootModel[str]):
    root: Annotated[str, Field(min_length=1)]


class Schema(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    session_id: Annotated[str, Field(min_length=1)]
    capabilities: Annotated[list[Capability], Field(min_length=1)]
    repository: identifier.Schema | None = None
    index_status: Annotated[str, Field(min_length=1)]
