"""
Generated Pydantic v2 models for Kiln JSON Schemas.

Do not edit this package by hand. Regenerate with:

    uv run generatemodels
"""

from __future__ import annotations

from enum import StrEnum
from typing import Annotated

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field

from . import configuration, reference


class RequestKind(StrEnum):
    initial_response = "initial_response"
    turn_response = "turn_response"
    tool_selection = "tool_selection"
    tool_result_followup = "tool_result_followup"
    output_production = "output_production"
    validation = "validation"
    recovery = "recovery"


class Schema(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    model_invocation_id: Annotated[
        str,
        Field(
            description="Operation-local identity for the model invocation this rendered request belongs to.",
            min_length=1,
        ),
    ]
    render_id: Annotated[
        str,
        Field(
            description="Context render identity used to produce the model request.",
            min_length=1,
        ),
    ]
    model_configuration: Annotated[
        configuration.SchemaModel1,
        Field(description="Model configuration selected for the invocation."),
    ]
    request_kind: Annotated[
        RequestKind | None,
        Field(description="Logical kind of model request being rendered."),
    ] = None
    rendered_messages_count: Annotated[
        int | None,
        Field(description="Number of messages rendered into the model request.", ge=0),
    ] = None
    rendered_tool_count: Annotated[
        int | None,
        Field(
            description="Number of tool definitions rendered into the model request.",
            ge=0,
        ),
    ] = None
    rendered_token_estimate: Annotated[
        int,
        Field(
            description="Estimated number of input tokens in the rendered model request.",
            ge=0,
        ),
    ]
    request_artifact_reference: Annotated[
        reference.Schema | None,
        Field(
            description="Optional artifact reference for the rendered model request."
        ),
    ] = None
    rendered_at: Annotated[
        AwareDatetime, Field(description="When the model request was rendered.")
    ]
