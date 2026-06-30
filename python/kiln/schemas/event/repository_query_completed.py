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
from . import usage as usage_1


class QueryKind(StrEnum):
    search = "search"
    source = "source"
    content = "content"
    version = "version"
    diagnostics = "diagnostics"


class ResultSummary(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    result_count: Annotated[
        int, Field(description="Number of results returned by the query.", ge=0)
    ]
    bytes_returned: Annotated[
        int | None,
        Field(description="Approximate number of bytes returned by the query.", ge=0),
    ] = None
    estimated_tokens_returned: Annotated[
        int | None,
        Field(
            description="Estimated number of tokens represented by returned content.",
            ge=0,
        ),
    ] = None
    truncated: Annotated[
        bool | None, Field(description="Whether the result was truncated.")
    ] = None


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
        QueryKind, Field(description="Kind of repository query that completed.")
    ]
    result_summary: Annotated[
        ResultSummary, Field(description="Summary of repository query results.")
    ]
    result_reference: Annotated[
        reference.Schema | None,
        Field(description="Optional artifact reference for the durable query result."),
    ] = None
    usage: Annotated[
        usage_1.SchemaModel,
        Field(description="Repository-specific telemetry for the completed query."),
    ]
    budget_usage: Annotated[
        usage_1.Schema | None,
        Field(description="Budget usage committed for this repository query."),
    ] = None
    completed_at: Annotated[
        AwareDatetime, Field(description="When the repository query completed.")
    ]
