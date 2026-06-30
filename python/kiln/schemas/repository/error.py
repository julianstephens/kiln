"""
Generated Pydantic v2 models for Kiln JSON Schemas.

Do not edit this package by hand. Regenerate with:

    uv run generatemodels
"""

from __future__ import annotations

from enum import StrEnum
from typing import Annotated, Any

from pydantic import BaseModel, ConfigDict, Field

from . import diagnostic, diagnostic_log_reference


class Category(StrEnum):
    protocol = "protocol"
    authorization = "authorization"
    session = "session"
    version = "version"
    repository = "repository"
    indexing = "indexing"
    parsing = "parsing"
    search = "search"
    graph = "graph"
    representation = "representation"
    resource = "resource"
    persistence = "persistence"
    cancellation = "cancellation"
    internal = "internal"


class Schema(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    code: Annotated[str, Field(min_length=1)]
    category: Category
    message: Annotated[str, Field(min_length=1)]
    retryable: bool
    operation_id: Annotated[str, Field(min_length=1)]
    repository_session_id: Annotated[str, Field(min_length=1)]
    repository_version: dict[str, Any]
    workspace_version: dict[str, Any]
    diagnostics: list[diagnostic.Schema]
    artifact_references: list[diagnostic_log_reference.Schema]
    cause_error_id: Annotated[str | None, Field(min_length=1)] = None
