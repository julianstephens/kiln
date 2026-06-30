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
        str | None,
        Field(
            description="The last fatal startup error that occurred, if any.",
            min_length=1,
        ),
    ] = None
