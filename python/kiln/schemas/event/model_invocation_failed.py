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
from . import reference, usage


class FailureCategory(StrEnum):
    provider_error = "provider_error"
    timeout = "timeout"
    rate_limited = "rate_limited"
    quota_exceeded = "quota_exceeded"
    content_filter = "content_filter"
    egress_denied = "egress_denied"
    invalid_request = "invalid_request"
    adapter_error = "adapter_error"
    canceled = "canceled"
    unknown = "unknown"


class Schema(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    model_invocation_id: Annotated[
        str, Field(description="Model invocation that failed.", min_length=1)
    ]
    failure_category: Annotated[
        FailureCategory,
        Field(description="Normalized model invocation failure category."),
    ]
    error: Annotated[
        error_1.Schema,
        Field(description="Run-level error describing the failed model invocation."),
    ]
    partial_response_artifact_reference: Annotated[
        reference.Schema | None,
        Field(
            description="Optional artifact reference for partial model output received before failure."
        ),
    ] = None
    budget_usage: Annotated[
        usage.Schema | None,
        Field(description="Budget usage committed before this invocation failed."),
    ] = None
    retryable: Annotated[
        bool | None,
        Field(description="Whether this failure may be retried by the runtime."),
    ] = None
    latency_ms: Annotated[
        int | None,
        Field(
            description="Elapsed invocation latency before failure in milliseconds.",
            ge=0,
        ),
    ] = None
    failed_at: Annotated[
        AwareDatetime, Field(description="When the model invocation failed.")
    ]
