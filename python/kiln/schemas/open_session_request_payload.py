"""
Generated Pydantic v2 models for Kiln JSON Schemas.

Do not edit this package by hand. Regenerate with:

    uv run generatemodels
"""

from __future__ import annotations

from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

from . import identifier


class AllowedOperation(StrEnum):
    repository_search = "repository.search"
    repository_get_source = "repository.get_source"
    repository_get_content = "repository.get_content"
    repository_get_version = "repository.get_version"
    repository_get_diagnostics = "repository.get_diagnostics"


class Schema(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    run_id: Annotated[
        str,
        Field(
            description="The run identifier for the run that is requesting to open a session",
            min_length=1,
        ),
    ]
    repository: Annotated[
        identifier.Schema,
        Field(
            description="The repository identifier for the repository to open a session for"
        ),
    ]
    allowed_operations: Annotated[
        list[AllowedOperation],
        Field(
            description="Concrete repository operations allowed for the opened session.",
            min_length=1,
        ),
    ]
