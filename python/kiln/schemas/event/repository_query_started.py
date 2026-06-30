"""
Generated Pydantic v2 models for Kiln JSON Schemas.

Do not edit this package by hand. Regenerate with:

    uv run generatemodels
"""

from __future__ import annotations

from enum import StrEnum
from typing import Annotated

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field

from . import reference


class QueryKind(StrEnum):
    search = "search"
    source = "source"
    content = "content"
    version = "version"
    diagnostics = "diagnostics"


class QuerySummary(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    mode: Annotated[str | None, Field(min_length=1)] = None
    target: Annotated[str | None, Field(min_length=1)] = None
    limit: Annotated[int | None, Field(ge=1)] = None


class Schema(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    repository_session_id: Annotated[
        str, Field(description="Repository session used for the query.", min_length=1)
    ]
    query_operation_id: Annotated[
        str,
        Field(
            description="Operation identity for this repository query.", min_length=1
        ),
    ]
    query_kind: Annotated[
        QueryKind, Field(description="Kind of repository query being executed.")
    ]
    query_request_reference: Annotated[
        reference.Schema | None,
        Field(
            description="Optional artifact reference for the query request when the request is stored durably."
        ),
    ] = None
    query_summary: Annotated[
        QuerySummary | None,
        Field(description="Small non-sensitive summary of the query."),
    ] = None
    query_started_at: Annotated[
        AwareDatetime, Field(description="When the repository query started.")
    ]
