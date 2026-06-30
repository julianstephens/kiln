"""
Generated Pydantic v2 models for Kiln JSON Schemas.

Do not edit this package by hand. Regenerate with:

    uv run generatemodels
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, RootModel

from . import version


class WorkspaceVersion(RootModel[version.Schema]):
    root: version.Schema


class KilnWorkspaceGeneratedPythonModelsBundle(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    workspace_version: WorkspaceVersion | None = None
