"""
Generated Pydantic v2 models for Kiln JSON Schemas.

Do not edit this package by hand. Regenerate with:

    uv run generatemodels
"""

from __future__ import annotations

from enum import StrEnum
from typing import Annotated

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field

from . import identifier


class Mode(StrEnum):
    static = "static"
    time_based = "time_based"
    event_driven = "event_driven"
    manual = "manual"


class RefreshTrigger(StrEnum):
    adapter_registered = "adapter_registered"
    adapter_removed = "adapter_removed"
    adapter_health_changed = "adapter_health_changed"
    protocol_capability_changed = "protocol_capability_changed"
    database_schema_changed = "database_schema_changed"
    configuration_changed = "configuration_changed"
    runtime_upgraded = "runtime_upgraded"


class RequestedRefreshPolicy(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    mode: Annotated[Mode, Field(description="How readiness metadata is refreshed.")]
    ttl_seconds: Annotated[
        int | None,
        Field(
            description="How long this readiness metadata should be considered fresh. Required for time_based refresh.",
            ge=1,
        ),
    ] = None
    refresh_after: Annotated[
        AwareDatetime | None,
        Field(
            description="Absolute timestamp after which this readiness metadata should be refreshed."
        ),
    ] = None
    refresh_triggers: Annotated[
        list[RefreshTrigger] | None,
        Field(
            description="Events or conditions that should cause this readiness metadata to be refreshed.",
            min_length=1,
        ),
    ] = None
    last_refreshed_at: Annotated[
        AwareDatetime | None,
        Field(description="When this readiness metadata was last refreshed."),
    ] = None


class Schema(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    repository: Annotated[
        identifier.Schema, Field(description="The repository that is being prepared.")
    ]
    requested_revision: Annotated[
        str, Field(description="The revision that is being prepared.", min_length=1)
    ]
    expected_digest: Annotated[
        str,
        Field(
            description="The expected digest of the repository at the requested revision.",
            min_length=1,
        ),
    ]
    indexing_configuration_id: Annotated[
        str,
        Field(
            description="The identifier of the indexing configuration that is being used to prepare the repository.",
            min_length=1,
        ),
    ]
    requested_refresh_policy: Annotated[
        RequestedRefreshPolicy,
        Field(
            description="Policy describing when this runtime session readiness description should be refreshed."
        ),
    ]
