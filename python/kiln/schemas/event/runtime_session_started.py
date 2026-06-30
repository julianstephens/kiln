"""
Generated Pydantic v2 models for Kiln JSON Schemas.

Do not edit this package by hand. Regenerate with:

    uv run generatemodels
"""

from __future__ import annotations

from enum import StrEnum
from typing import Annotated

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field


class ProcessKind(StrEnum):
    python_sdk = "python_sdk"
    cli = "cli"
    hosted_worker = "hosted_worker"
    test_harness = "test_harness"
    unknown = "unknown"


class ParentProcess(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    process_kind: Annotated[
        ProcessKind,
        Field(
            description="The kind of parent process that launched the runtime session."
        ),
    ]
    process_id: Annotated[
        int | None,
        Field(
            description="The operating-system process ID of the parent process, when safe and available.",
            ge=1,
        ),
    ] = None
    process_start_time: Annotated[
        AwareDatetime | None,
        Field(description="When the parent process started, when safe and available."),
    ] = None
    executable_name: Annotated[
        str | None,
        Field(
            description="The executable or logical entrypoint name of the parent process.",
            min_length=1,
        ),
    ] = None
    supervisor_id: Annotated[
        str | None,
        Field(
            description="Stable identity for the supervising component, worker, or SDK instance, when available.",
            min_length=1,
        ),
    ] = None
    host_id: Annotated[
        str | None,
        Field(
            description="Opaque host or container identity, when safe to record.",
            min_length=1,
        ),
    ] = None
    sdk_version: Annotated[
        str | None,
        Field(
            description="Version of the SDK or client package that launched the runtime session, when applicable.",
            min_length=1,
        ),
    ] = None
    command_invocation_id: Annotated[
        str | None,
        Field(
            description="Opaque identity for the CLI or command invocation that launched the runtime session, when applicable.",
            min_length=1,
        ),
    ] = None


class StartupMode(StrEnum):
    fresh = "fresh"
    resume = "resume"
    restart = "restart"
    recovery = "recovery"
    test = "test"


class Schema(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    runtime_session_id: Annotated[
        str, Field(description="The runtime session that was started.", min_length=1)
    ]
    runtime_version: Annotated[
        str, Field(description="Runtime implementation version.", min_length=1)
    ]
    protocol_version: Annotated[
        str,
        Field(
            description="Protocol version spoken by this runtime session.", min_length=1
        ),
    ]
    parent_process: Annotated[
        ParentProcess,
        Field(
            description="Identity metadata for the parent process that launched or supervised this runtime session."
        ),
    ]
    database_id: Annotated[
        str,
        Field(
            description="Opaque identity for the database or persistence store used by the runtime session.",
            min_length=1,
        ),
    ]
    database_schema_version: Annotated[
        str | None,
        Field(
            description="Database schema version observed at session startup, when available.",
            min_length=1,
        ),
    ] = None
    startup_timestamp: Annotated[
        AwareDatetime,
        Field(description="When runtime session startup began or was recorded."),
    ]
    startup_mode: Annotated[
        StartupMode | None, Field(description="How the runtime session was started.")
    ] = None
    startup_reason: Annotated[
        str | None,
        Field(
            description="Human-readable or system-provided reason for starting the runtime session.",
            min_length=1,
        ),
    ] = None
