"""
Generated Pydantic v2 models for Kiln JSON Schemas.

Do not edit this package by hand. Regenerate with:

    uv run generatemodels
"""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field

from . import terminal_result_reference, usage
from . import validation_report_reference as validation_report_reference_1


class StopReason(BaseModel):
    category: Literal["completed"] | None = None


class Schema(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    stop_reason: StopReason
    final_result_reference: Annotated[
        terminal_result_reference.Schema,
        Field(
            description="The terminal result reference that was produced by this run"
        ),
    ]
    final_usage: Annotated[
        usage.Schema,
        Field(description="The usage summary that was produced by this run"),
    ]
    validation_report_reference: Annotated[
        validation_report_reference_1.Schema | None,
        Field(
            description="The validation report reference that was produced by this run"
        ),
    ] = None
