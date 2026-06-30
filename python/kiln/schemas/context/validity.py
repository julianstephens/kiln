"""
Generated Pydantic v2 models for Kiln JSON Schemas.

Do not edit this package by hand. Regenerate with:

    uv run generatemodels
"""

from __future__ import annotations

from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field


class ContentStatus(StrEnum):
    current = "current"
    stale = "stale"


class SynchronizationStatus(StrEnum):
    synchronized = "synchronized"
    out_of_sync = "out_of_sync"


class ContentCompleteness(StrEnum):
    complete = "complete"
    truncated = "truncated"


class Schema(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    content_status: ContentStatus | None = None
    version: Annotated[str | None, Field(min_length=1)] = None
    invalidation_reason: Annotated[str | None, Field(min_length=1)] = None
    synchronization_status: SynchronizationStatus | None = None
    content_completeness: ContentCompleteness | None = None
