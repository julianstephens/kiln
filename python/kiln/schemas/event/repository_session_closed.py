"""
Generated Pydantic v2 models for Kiln JSON Schemas.

Do not edit this package by hand. Regenerate with:

    uv run generatemodels
"""

from __future__ import annotations

from enum import StrEnum
from typing import Annotated

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field

from . import diagnostic_log_reference as diagnostic_log_reference_1
from . import error as error_1
from . import preparation_status, version
from . import usage as usage_1


class CloseReason(StrEnum):
    completed = "completed"
    canceled = "canceled"
    failed = "failed"
    expired = "expired"
    superseded = "superseded"
    runtime_shutdown = "runtime_shutdown"
    unknown = "unknown"


class Schema(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    repository_session_id: Annotated[
        str, Field(description="Repository session that was closed.", min_length=1)
    ]
    close_reason: Annotated[
        CloseReason, Field(description="Reason the repository session was closed.")
    ]
    final_repository_version: Annotated[
        version.SchemaModel1 | None,
        Field(
            description="Final repository version observed before closing the session."
        ),
    ] = None
    final_preparation_status: Annotated[
        preparation_status.Schema | None,
        Field(
            description="Final preparation status observed before closing the session."
        ),
    ] = None
    usage: Annotated[
        usage_1.SchemaModel | None,
        Field(
            description="Repository-specific telemetry accumulated for the session, when available."
        ),
    ] = None
    budget_usage: Annotated[
        usage_1.Schema | None,
        Field(
            description="Budget usage committed for the repository session, when available."
        ),
    ] = None
    error: Annotated[
        error_1.SchemaModel | None,
        Field(
            description="Repository error associated with the closed session, when the session closed because of failure."
        ),
    ] = None
    diagnostic_log_reference: Annotated[
        diagnostic_log_reference_1.Schema | None,
        Field(
            description="Optional diagnostic log artifact for the repository session."
        ),
    ] = None
    closed_at: Annotated[
        AwareDatetime, Field(description="When the repository session was closed.")
    ]
