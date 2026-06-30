"""
Generated Pydantic v2 models for Kiln JSON Schemas.

Do not edit this package by hand. Regenerate with:

    uv run generatemodels
"""

from __future__ import annotations

from enum import StrEnum
from typing import Annotated, Any

from pydantic import BaseModel, ConfigDict, Field


class Category(StrEnum):
    completed = "completed"
    failed = "failed"
    canceled = "canceled"
    exhausted = "exhausted"


class Code(StrEnum):
    completed_successfully = "completed_successfully"
    user_canceled = "user_canceled"
    system_canceled = "system_canceled"
    policy_canceled = "policy_canceled"
    budget_exhausted = "budget_exhausted"
    turn_limit_exhausted = "turn_limit_exhausted"
    time_limit_exhausted = "time_limit_exhausted"
    context_limit_exhausted = "context_limit_exhausted"
    retry_limit_exhausted = "retry_limit_exhausted"
    validation_failed = "validation_failed"
    capability_denied = "capability_denied"
    capability_unavailable = "capability_unavailable"
    repository_unavailable = "repository_unavailable"
    repository_dirty = "repository_dirty"
    tool_failed = "tool_failed"
    external_operation_failed = "external_operation_failed"
    output_production_failed = "output_production_failed"
    internal_error = "internal_error"
    runtime_interrupted = "runtime_interrupted"
    worker_interrupted = "worker_interrupted"
    shutdown_interrupted = "shutdown_interrupted"
    lease_lost = "lease_lost"
    validation_error = "validation_error"


class Schema(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    category: Annotated[
        Category, Field(description="Broad class of reason the run stopped.")
    ]
    code: Annotated[Code, Field(description="Specific machine-readable stop reason.")]
    message: Annotated[
        str | None,
        Field(
            description="Optional human-readable explanation of the stop reason.",
            min_length=1,
        ),
    ] = None
    details: Annotated[
        dict[str, Any] | None,
        Field(
            description="Optional structured diagnostic details for the stop reason."
        ),
    ] = None
