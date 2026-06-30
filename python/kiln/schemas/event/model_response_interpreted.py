"""
Generated Pydantic v2 models for Kiln JSON Schemas.

Do not edit this package by hand. Regenerate with:

    uv run generatemodels
"""

from __future__ import annotations

from enum import StrEnum
from typing import Annotated

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field

from . import reference


class InterpretationKind(StrEnum):
    assistant_message = "assistant_message"
    tool_call_request = "tool_call_request"
    final_answer_candidate = "final_answer_candidate"
    patch_candidate = "patch_candidate"
    report_candidate = "report_candidate"
    validation_judgment = "validation_judgment"
    unstructured = "unstructured"


class ToolCallRequest(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    tool_call_id: Annotated[str, Field(min_length=1)]
    tool_name: Annotated[str, Field(min_length=1)]
    arguments_artifact_reference: Annotated[
        reference.Schema | None,
        Field(description="Optional artifact reference for tool-call arguments."),
    ] = None


class InterpretationWarning(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    code: Annotated[str, Field(min_length=1)]
    message: Annotated[str, Field(min_length=1)]


class Schema(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    model_invocation_id: Annotated[
        str,
        Field(
            description="Model invocation whose response was interpreted.", min_length=1
        ),
    ]
    response_artifact_reference: Annotated[
        reference.Schema,
        Field(description="Artifact reference for the raw model response."),
    ]
    interpretation_kind: Annotated[
        InterpretationKind,
        Field(description="Primary interpretation produced from the model response."),
    ]
    interpreted_output_reference: Annotated[
        reference.Schema | None,
        Field(
            description="Optional artifact reference for the normalized interpreted output."
        ),
    ] = None
    tool_call_requests: Annotated[
        list[ToolCallRequest] | None,
        Field(
            description="Tool calls requested by the interpreted response.",
            min_length=1,
        ),
    ] = None
    interpretation_warnings: Annotated[
        list[InterpretationWarning] | None,
        Field(
            description="Non-fatal warnings produced while interpreting the model response.",
            min_length=1,
        ),
    ] = None
    interpreted_at: Annotated[
        AwareDatetime, Field(description="When the model response was interpreted.")
    ]
