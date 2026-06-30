"""
Generated Pydantic v2 models for Kiln JSON Schemas.

Do not edit this package by hand. Regenerate with:

    uv run generatemodels
"""

from __future__ import annotations

from enum import StrEnum
from typing import Annotated

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field

from . import identifier, version
from . import preparation_status as preparation_status_1


class SupportedOperation(StrEnum):
    repository_search = "repository.search"
    repository_source = "repository.source"
    repository_version = "repository.version"
    repository_diagnostics = "repository.diagnostics"


class Schema(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    repository_session_id: Annotated[
        str, Field(description="Repository session that was opened.", min_length=1)
    ]
    repository: Annotated[
        identifier.Schema,
        Field(description="Repository associated with the opened session."),
    ]
    repository_version: Annotated[
        version.SchemaModel1,
        Field(description="Repository version observed when the session was opened."),
    ]
    preparation_status: Annotated[
        preparation_status_1.Schema,
        Field(description="Preparation status available for the opened session."),
    ]
    supported_operations: Annotated[
        list[SupportedOperation] | None,
        Field(
            description="Repository operations available for this session.",
            min_length=1,
        ),
    ] = None
    opened_at: Annotated[
        AwareDatetime, Field(description="When the repository session was opened.")
    ]
