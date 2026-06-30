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
            description="Operation-local identity for this model invocation.",
            min_length=1,
        ),
    ]
    model_configuration: Annotated[
        configuration.SchemaModel1,
        Field(description="Model configuration used for the invocation."),
    ]
    request_artifact_reference: Annotated[
        reference.Schema,
        Field(
            description="Artifact reference for the rendered model request sent to the model adapter or provider."
        ),
    ]
    request_kind: Annotated[
        RequestKind | None,
        Field(description="Logical kind of model request being invoked."),
    ] = None
    input_token_estimate: Annotated[
        int, Field(description="Estimated input tokens sent to the model.", ge=0)
    ]
    streaming_enabled: Annotated[
        bool | None,
        Field(description="Whether this invocation requested streaming output."),
    ] = None
    started_at: Annotated[
        AwareDatetime, Field(description="When the model invocation started.")
    ]
