"""
Generated Pydantic v2 models for Kiln JSON Schemas.

Do not edit this package by hand. Regenerate with:

    uv run generatemodels
"""

from __future__ import annotations

from typing import Annotated, Any

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field

from . import (
    artifact_events,
    budget_events,
    context_events,
    model_events,
    reference,
    repository_events,
    run_lifecycle_events,
    runtime_session_events,
    turn_events,
)


class Schema(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    event_id: Annotated[
        str,
        Field(
            description="A globally unique identifier with the installation or tenant scope for this event",
            min_length=1,
        ),
    ]
    event_schema_version: Annotated[
        str,
        Field(
            description="The version of the event schema for this event_type.",
            min_length=1,
        ),
    ]
    run_id: Annotated[
        str | None,
        Field(description="The run that this event is associated with", min_length=1),
    ] = None
    sequence: Annotated[
        int,
        Field(
            description="The monotonically increasing sequence number of this event within the run",
            ge=1,
        ),
    ]
    event_type: Annotated[
        run_lifecycle_events.Schema
        | runtime_session_events.Schema
        | repository_events.Schema
        | context_events.Schema
        | model_events.Schema
        | budget_events.Schema
        | turn_events.Schema
        | artifact_events.Schema,
        Field(description="The type of event being reported"),
    ]
    occurred_at: Annotated[
        AwareDatetime,
        Field(description="The timestamp of when this event was generated"),
    ]
    producer: Annotated[
        str,
        Field(
            description="The identifier of the logical component that generated this event",
            min_length=1,
        ),
    ]
    payload: Annotated[
        dict[str, Any],
        Field(
            description="The payload of the event, which varies based on the event type"
        ),
    ]
    causation_id: Annotated[
        str | None,
        Field(
            description="The event_id of the event that caused this event to be generated, if applicable",
            min_length=1,
        ),
    ] = None
    correlation_id: Annotated[
        str | None,
        Field(
            description="An identifier that can be used to correlate this event with other events, if applicable",
            min_length=1,
        ),
    ] = None
    operation_id: Annotated[
        str | None,
        Field(
            description="An identifier that can be used to associate this event with a specific operation, if applicable",
            min_length=1,
        ),
    ] = None
    turn_id: Annotated[
        str | None,
        Field(
            description="An identifier that can be used to associate this event with a specific turn, if applicable",
            min_length=1,
        ),
    ] = None
    repository_session_id: Annotated[
        str | None,
        Field(
            description="An identifier that can be used to associate this event with a specific repository session, if applicable",
            min_length=1,
        ),
    ] = None
    artifact_references: Annotated[
        list[reference.Schema] | None,
        Field(
            description="References to any artifacts that are associated with this event",
            min_length=1,
        ),
    ] = None
