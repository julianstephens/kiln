"""
Generated Pydantic v2 models for Kiln JSON Schemas.

Do not edit this package by hand. Regenerate with:

    uv run generatemodels
"""

from __future__ import annotations

from enum import StrEnum
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field

from . import error, error_category, lifecycle_state, reference


class StopReason(BaseModel):
    category: Literal["failed"] | None = None


class CleanupStatus(StrEnum):
    not_required = "not_required"
    pending = "pending"
    completed = "completed"
    failed = "failed"
    unknown = "unknown"


class Schema(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    stop_reason: StopReason
    failure_category: Annotated[
        error_category.Schema,
        Field(description="The category of failure that caused this run to stop"),
    ]
    last_successful_lifecycle_state: Annotated[
        lifecycle_state.Schema,
        Field(
            description="The last successful lifecycle state that this run was in before it failed"
        ),
    ]
    failure_detail: Annotated[
        error.Schema | None,
        Field(
            description="Additional details about the failure that caused this run to stop"
        ),
    ] = None
    partial_result_references: Annotated[
        list[reference.Schema] | None,
        Field(
            description="The artifact references that contain partial results produced by this run before it failed"
        ),
    ] = None
    cleanup_status: Annotated[
        CleanupStatus,
        Field(description="The status of the cleanup process for this run"),
    ]
