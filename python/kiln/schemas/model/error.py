"""
Generated Pydantic v2 models for Kiln JSON Schemas.

Do not edit this package by hand. Regenerate with:

    uv run generatemodels
"""

from __future__ import annotations

from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

from . import diagnostic_log_reference, reference


class Category(StrEnum):
    invalid_request = "invalid_request"
    authentication = "authentication"
    authorization = "authorization"
    rate_limited = "rate_limited"
    quota_exceeded = "quota_exceeded"
    timeout = "timeout"
    provider_unavailable = "provider_unavailable"
    model_unavailable = "model_unavailable"
    content_filter = "content_filter"
    egress_denied = "egress_denied"
    context_length_exceeded = "context_length_exceeded"
    adapter_error = "adapter_error"
    canceled = "canceled"
    unknown = "unknown"


class Schema(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    error_id: Annotated[
        str, Field(description="Stable identity for this model error.", min_length=1)
    ]
    category: Annotated[
        Category, Field(description="Provider-neutral model error category.")
    ]
    code: Annotated[
        str,
        Field(
            description="Provider-neutral or adapter-normalized error code.",
            min_length=1,
        ),
    ]
    provider_code: Annotated[
        str | None,
        Field(
            description="Provider-specific error code, when safe to expose.",
            min_length=1,
        ),
    ] = None
    message: Annotated[
        str,
        Field(
            description="Human-readable provider-neutral error message.", min_length=1
        ),
    ]
    retryable: Annotated[
        bool, Field(description="Whether the model invocation may be retried.")
    ]
    retry_after_seconds: Annotated[
        int | None,
        Field(description="Suggested retry delay in seconds, when available.", ge=0),
    ] = None
    model_id: Annotated[
        str | None,
        Field(
            description="Model identifier associated with the failure, when known.",
            min_length=1,
        ),
    ] = None
    provider_id: Annotated[
        str | None,
        Field(
            description="Provider associated with the failure, when known.",
            min_length=1,
        ),
    ] = None
    model_invocation_id: Annotated[
        str | None,
        Field(
            description="Model invocation associated with the failure, when known.",
            min_length=1,
        ),
    ] = None
    partial_response_artifact_reference: Annotated[
        reference.Schema | None,
        Field(
            description="Artifact reference for partial model response content, when available."
        ),
    ] = None
    diagnostic_artifact_reference: Annotated[
        diagnostic_log_reference.Schema | None,
        Field(
            description="Artifact reference for model diagnostic details, when available."
        ),
    ] = None
