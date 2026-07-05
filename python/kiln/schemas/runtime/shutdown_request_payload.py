"""
Generated Pydantic v2 models for Kiln JSON Schemas.

Do not edit this package by hand. Regenerate with:

    uv run generatemodels
"""

from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field


class Schema(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    grace_period_seconds: Annotated[
        int,
        Field(
            description="The number of seconds to wait before shutting down the runtime. If not specified, the runtime will shut down immediately."
        ),
    ]
    cancel_in_flight_requests: Annotated[
        bool,
        Field(
            description="If true, the runtime will cancel any in-flight requests before shutting down. If false, the runtime will wait for in-flight requests to complete before shutting down."
        ),
    ]
    reason: Annotated[
        str, Field(description="A human-readable reason for the shutdown request.")
    ]
