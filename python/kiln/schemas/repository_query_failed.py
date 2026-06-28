"""
Generated Pydantic v2 models for Kiln JSON Schemas.

Do not edit this package by hand. Regenerate with:

    uv run generatemodels
"""

from __future__ import annotations

from enum import StrEnum
from typing import Annotated

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field

from . import error as error_1
from . import reference
from . import usage as usage_1


class QueryKind(StrEnum):
    search = "search"
    source = "source"
    content = "content"
    version = "version"
    diagnostics = "diagnostics"


class Schema(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    repository_session_id: Annotated[
        str,
        Field(
            description="Repository session used for the failed query.", min_length=1
        ),
    ]
    query_operation_id: Annotated[
        str,
        Field(
            description="Operation identity for this repository query.", min_length=1
        ),
    ]
    query_kind: Annotated[
        QueryKind, Field(description="Kind of repository query that failed.")
    ]
    error: Annotated[
        error_1.Schema,
        Field(description="Repository error produced by the failed query."),
    ]
    partial_result_reference: Annotated[
        reference.Schema | None,
        Field(
            description="Optional artifact reference for partial query results, if any were produced before failure."
        ),
    ] = None
    usage: Annotated[
        usage_1.SchemaModel | None,
        Field(
            description="Repository-specific telemetry recorded before the query failed."
        ),
    ] = None
    budget_usage: Annotated[
        usage_1.Schema | None,
        Field(description="Budget usage committed before the query failed."),
    ] = None
    failed_at: Annotated[
        AwareDatetime, Field(description="When the repository query failed.")
    ]
