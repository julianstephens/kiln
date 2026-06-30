"""
Generated Pydantic v2 models for Kiln JSON Schemas.

Do not edit this package by hand. Regenerate with:

    uv run generatemodels
"""

from __future__ import annotations

from enum import StrEnum
from typing import Annotated, Any

from pydantic import BaseModel, ConfigDict, Field

from . import diagnostic


class RefreshState(StrEnum):
    not_started = "not_started"
    in_progress = "in_progress"
    completed = "completed"
    failed = "failed"


class Schema(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    repository_version: dict[str, Any] | None = None
    workspace_version: dict[str, Any] | None = None
    current_index_state: Annotated[str | None, Field(min_length=1)] = None
    stale_file_count: Annotated[int | None, Field(ge=0)] = None
    refresh_state: RefreshState | None = None
    preparation_checkpoints: list[dict[str, Any]]
    diagnostics: list[diagnostic.Schema]
