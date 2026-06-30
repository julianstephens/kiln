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
    id: Annotated[str, Field(min_length=1)]
    workspace_id: Annotated[str | None, Field(min_length=1)] = None
    version_id: Annotated[str, Field(min_length=1)]
    workspace_version_id: Annotated[str, Field(min_length=1)]
