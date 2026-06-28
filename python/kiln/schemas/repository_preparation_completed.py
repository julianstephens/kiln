"""
Generated Pydantic v2 models for Kiln JSON Schemas.

Do not edit this package by hand. Regenerate with:

    uv run generatemodels
"""

from __future__ import annotations

from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

from . import diagnostic_log_reference as diagnostic_log_reference_1
from . import identifier, repository_snapshot_reference
from . import preparation_status as preparation_status_1
from . import usage as usage_1
from . import version as version_1


class PreparedCapability(StrEnum):
    search = "search"
    source = "source"
    open_session = "open_session"
    close_session = "close_session"
    version = "version"
    diagnostics = "diagnostics"


class Schema(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    repository_session_id: Annotated[
        str,
        Field(description="The repository session that was prepared.", min_length=1),
    ]
    repository: Annotated[
        identifier.Schema, Field(description="The repository that was prepared.")
    ]
    repository_version: Annotated[
        version_1.SchemaModel1,
        Field(description="The repository version available after preparation."),
    ]
    preparation_status: Annotated[
        preparation_status_1.Schema,
        Field(description="Final preparation status for the repository session."),
    ]
    prepared_capabilities: Annotated[
        list[PreparedCapability],
        Field(
            description="Repository protocol capabilities available after preparation.",
            min_length=1,
        ),
    ]
    preparation_duration_seconds: Annotated[
        float,
        Field(
            description="Elapsed wall-clock duration of repository preparation.", ge=0.0
        ),
    ]
    source_snapshot_reference: Annotated[
        repository_snapshot_reference.Schema | None,
        Field(
            description="Optional artifact reference for a repository snapshot produced during preparation."
        ),
    ] = None
    diagnostic_log_reference: Annotated[
        diagnostic_log_reference_1.Schema | None,
        Field(
            description="Optional diagnostic log artifact produced during preparation."
        ),
    ] = None
    usage: Annotated[
        usage_1.SchemaModel | None,
        Field(description="Repository-operation usage recorded during preparation."),
    ] = None
    budget_usage: Annotated[
        usage_1.Schema | None,
        Field(description="Budget usage committed for repository preparation."),
    ] = None
