"""
Generated Pydantic v2 models for Kiln JSON Schemas.

Do not edit this package by hand. Regenerate with:

    uv run generatemodels
"""

from __future__ import annotations

from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, RootModel


class SupportedProtocolCapability(StrEnum):
    repository_open_session = "repository.open_session"
    repository_search = "repository.search"
    repository_get_source = "repository.get_source"
    model_generate = "model.generate"
    capability_check = "capability.check"
    budget_reserve = "budget.reserve"
    budget_commit = "budget.commit"
    artifact_create = "artifact.create"
    artifact_read = "artifact.read"
    validation_request = "validation.request"
    workspace_read = "workspace.read"
    workspace_patch = "workspace.patch"


class AdapterKind(StrEnum):
    repository = "repository"
    model = "model"
    artifact = "artifact"
    budget = "budget"
    capability = "capability"
    workspace = "workspace"
    validation = "validation"
    telemetry = "telemetry"


class SupportedOperation(RootModel[str]):
    root: Annotated[str, Field(min_length=1)]


class CapabilityProfile(StrEnum):
    read_only = "read_only"
    read_write = "read_write"
    networked = "networked"
    sandboxed = "sandboxed"
    external = "external"
    unknown = "unknown"


class AvailableAdapter(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    adapter_id: Annotated[
        str, Field(description="Stable runtime-local adapter identity.", min_length=1)
    ]
    adapter_kind: Annotated[AdapterKind, Field(description="Logical adapter kind.")]
    adapter_version: Annotated[
        str, Field(description="Adapter implementation version.", min_length=1)
    ]
    supported_operations: Annotated[
        list[SupportedOperation] | None,
        Field(description="Operations supported by this adapter.", min_length=1),
    ] = None
    capability_profile: Annotated[
        CapabilityProfile | None,
        Field(description="Optional coarse capability profile exposed by the adapter."),
    ] = None


class Schema(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    runtime_session_id: Annotated[
        str, Field(description="The runtime session that is now ready.", min_length=1)
    ]
    supported_protocol_capabilities: Annotated[
        list[SupportedProtocolCapability],
        Field(
            description="Protocol capabilities supported by this runtime session.",
            min_length=1,
        ),
    ]
    database_schema_version: Annotated[
        str, Field(description="The loaded database schema version.", min_length=1)
    ]
    available_adapters: Annotated[
        list[AvailableAdapter],
        Field(description="Adapters available to the runtime session.", min_length=1),
    ]
