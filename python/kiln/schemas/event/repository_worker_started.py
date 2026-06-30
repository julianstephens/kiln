"""
Generated Pydantic v2 models for Kiln JSON Schemas.

Do not edit this package by hand. Regenerate with:

    uv run generatemodels
"""

from __future__ import annotations

from enum import StrEnum
from typing import Annotated

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field


class WorkerKind(StrEnum):
    local_git = "local_git"
    remote_git = "remote_git"
    index_service = "index_service"
    mock = "mock"
    unknown = "unknown"


class SupportedOperation(StrEnum):
    repository_open_session = "repository.open_session"
    repository_close_session = "repository.close_session"
    repository_prepare = "repository.prepare"
    repository_get_preparation_status = "repository.get_preparation_status"
    repository_get_version = "repository.get_version"
    repository_search = "repository.search"
    repository_get_source = "repository.get_source"
    repository_get_content = "repository.get_content"
    repository_get_diagnostics = "repository.get_diagnostics"


class SupportedRepositoryKind(StrEnum):
    git = "git"
    github = "github"
    filesystem = "filesystem"
    archive = "archive"
    unknown = "unknown"


class Schema(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    repository_worker_id: Annotated[
        str,
        Field(
            description="Runtime-local identity for the repository worker.",
            min_length=1,
        ),
    ]
    runtime_session_id: Annotated[
        str,
        Field(
            description="Runtime session that started this repository worker.",
            min_length=1,
        ),
    ]
    worker_kind: Annotated[WorkerKind, Field(description="Kind of repository worker.")]
    supported_operations: Annotated[
        list[SupportedOperation],
        Field(
            description="Repository protocol operations supported by this repository worker.",
            min_length=1,
        ),
    ]
    supported_repository_kinds: Annotated[
        list[SupportedRepositoryKind] | None,
        Field(description="Repository kinds this worker can handle.", min_length=1),
    ] = None
    worker_version: Annotated[
        str | None,
        Field(description="Repository worker implementation version.", min_length=1),
    ] = None
    started_at: Annotated[
        AwareDatetime, Field(description="When the repository worker started.")
    ]
