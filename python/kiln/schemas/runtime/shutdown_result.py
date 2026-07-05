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
    accepted: Annotated[
        bool,
        Field(
            description="Indicates whether the shutdown request was accepted by the runtime."
        ),
    ]
    draining: Annotated[
        bool,
        Field(
            description="Indicates whether the runtime is currently draining in-flight requests before shutting down."
        ),
    ]
    shutdown: Annotated[
        bool,
        Field(
            description="Indicates whether the runtime has completed the shutdown process."
        ),
    ]
    in_flight_request_count: Annotated[
        int,
        Field(
            description="The number of in-flight requests currently being processed by the runtime."
        ),
    ]
