"""
Generated Pydantic v2 models for Kiln JSON Schemas.

Do not edit this package by hand. Regenerate with:

    uv run generatemodels
"""

from __future__ import annotations

from enum import StrEnum
from typing import Annotated, Any

from pydantic import BaseModel, ConfigDict, Field, RootModel

from . import (
    error,
    initialize_request_payload,
    initialize_result,
    shutdown_request_payload,
    shutdown_result,
)


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
        dict[str, Any], Field(description="Additional details about the error.")
    ]
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


class RuntimeError(RootModel[error.Schema]):
    root: error.Schema


class RuntimeInitializeRequestPayload(RootModel[initialize_request_payload.Schema]):
    root: initialize_request_payload.Schema


class RuntimeInitializeResult(RootModel[initialize_result.Schema]):
    root: initialize_result.Schema


class RuntimeShutdownRequestPayload(RootModel[shutdown_request_payload.Schema]):
    root: shutdown_request_payload.Schema


class RuntimeShutdownResult(RootModel[shutdown_result.Schema]):
    root: shutdown_result.Schema


class KilnRuntimeGeneratedPythonModelsBundle(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    runtime_error: RuntimeError | None = None
    runtime_health_result: RuntimeHealthResult | None = None
    runtime_initialize_request_payload: RuntimeInitializeRequestPayload | None = None
    runtime_initialize_result: RuntimeInitializeResult | None = None
    runtime_shutdown_request_payload: RuntimeShutdownRequestPayload | None = None
    runtime_shutdown_result: RuntimeShutdownResult | None = None


class Schema(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    initialized: Annotated[
        bool, Field(description="Whether the runtime has been initialized.")
    ]
    ready: Annotated[
        bool, Field(description="Whether the runtime is ready to accept requests.")
    ]
    draining: Annotated[
        bool, Field(description="Whether the runtime is in the process of draining.")
    ]
    shutdown: Annotated[
        bool,
        Field(description="Whether the runtime is in the process of shutting down."),
    ]
    last_fatal_startup_error: Annotated[
        KilnError | None,
        Field(description="The last fatal startup error that occurred, if any."),
    ] = None


class RuntimeHealthResult(RootModel[Schema]):
    root: Schema
