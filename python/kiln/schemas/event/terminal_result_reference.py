"""
Generated Pydantic v2 models for Kiln JSON Schemas.

Do not edit this package by hand. Regenerate with:

    uv run generatemodels
"""

from __future__ import annotations

from enum import StrEnum
from typing import Annotated

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field


class Kind(StrEnum):
    output = "output"
    error = "error"
    cancellation = "cancellation"
    exhaustion = "exhaustion"


class Schema(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    kind: Annotated[
        Kind, Field(description="The kind of terminal result being referenced.")
    ]
    id: Annotated[
        str,
        Field(
            description="Stable identifier for the persisted terminal result.",
            min_length=1,
        ),
    ]
    created_at: Annotated[
        AwareDatetime | None,
        Field(description="When the terminal result was recorded."),
    ] = None
