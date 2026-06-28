"""
Generated Pydantic v2 models for Kiln JSON Schemas.

Do not edit this package by hand. Regenerate with:

    uv run generatemodels
"""

from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

from . import version


class Schema(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    repository_session_id: Annotated[
        str,
        Field(
            description="The repository session that is being used to execute this run",
            min_length=1,
        ),
    ]
    repository_version: Annotated[
        version.SchemaModel1,
        Field(
            description="The version of the repository that is being used to execute this run"
        ),
    ]
    workspace_version: Annotated[
        version.SchemaModel2,
        Field(
            description="The version of the workspace that is being used to execute this run"
        ),
    ]
    initial_turn_id: Annotated[
        str,
        Field(
            description="The turn that is being used to execute this run", min_length=1
        ),
    ]
