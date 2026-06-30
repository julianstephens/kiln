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
    compatibility = "compatibility"
    validation = "validation"
    lifecycle = "lifecycle"
    shutdown = "shutdown"
    internal = "internal"


class KilnError(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    code: Annotated[
        str, Field(description="The error code.", min_length=1, pattern="^runtime\\.")
    ]
    category: Annotated[Category, Field(description="The error category.")]
    message: Annotated[
        str,
        Field(
            description="A human-readable message describing the error.", min_length=1
        ),
    ]
    retryable: Annotated[bool, Field(description="Whether the error is retryable.")]
    details: Annotated[
        dict[str, Any] | None, Field(description="Additional details about the error.")
    ] = None
    correlation_id: Annotated[
        str | None,
        Field(
            description="A correlation ID for the error, if available.", min_length=1
        ),
    ] = None
    runtime_id: Annotated[
        str | None,
        Field(
            description="The unique identifier of the runtime that generated the error.",
            min_length=1,
        ),
    ] = None


class Schema(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    kiln_error: Annotated[
        KilnError, Field(description="Information about the error that occurred.")
    ]
