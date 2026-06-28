"""
Generated Pydantic v2 models for Kiln JSON Schemas.

Do not edit this package by hand. Regenerate with:

    uv run generatemodels
"""

from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, RootModel


class RequestedAdapter(RootModel[str]):
    root: Annotated[str, Field(min_length=1)]


class Schema(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    initialized_operation_id: Annotated[
        str,
        Field(
            description="The operation that is being performed to initialize this run",
            min_length=1,
        ),
    ]
    runtime_session_id: Annotated[
        str,
        Field(
            description="The runtime session that is being used to initialize this run",
            min_length=1,
        ),
    ]
    requested_adapters: Annotated[
        list[RequestedAdapter] | None,
        Field(
            description="The adapters that were requested for this run", min_length=1
        ),
    ] = None
