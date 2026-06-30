"""
Generated Pydantic v2 models for Kiln JSON Schemas.

Do not edit this package by hand. Regenerate with:

    uv run generatemodels
"""

from __future__ import annotations

from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field


class Mode(StrEnum):
    installation_default = "installation_default"
    unlimited = "unlimited"
    custom = "custom"


class Schema(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    mode: Mode
    model_input_tokens: Annotated[int | None, Field(ge=0)] = None
    model_output_tokens: Annotated[int | None, Field(ge=0)] = None
    model_calls: Annotated[int | None, Field(ge=0)] = None
    tool_calls: Annotated[int | None, Field(ge=0)] = None
    repository_requests: Annotated[int | None, Field(ge=0)] = None
    elapsed_wall_time_seconds: Annotated[float | None, Field(ge=0.0)] = None
    monetary_cost_usd: Annotated[float | None, Field(ge=0.0)] = None
    command_time_seconds: Annotated[float | None, Field(ge=0.0)] = None
    command_output_size_bytes: Annotated[int | None, Field(ge=0)] = None
    artifact_size_bytes: Annotated[int | None, Field(ge=0)] = None
    repeated_token_cost_usd: Annotated[float | None, Field(ge=0.0)] = None
