"""
Generated Pydantic v2 models for Kiln JSON Schemas.

Do not edit this package by hand. Regenerate with:

    uv run generatemodels
"""

from __future__ import annotations

from enum import StrEnum
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, RootModel

from . import repository_snapshot_reference


class ContentType(StrEnum):
    inline = "inline"
    artifact = "artifact"
    structured_representation = "structured_representation"


class Schema(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    content_type: Literal["inline"]
    inline: Annotated[str, Field(min_length=1)]
    artifact_reference: repository_snapshot_reference.Schema | None = None
    structured_representation: dict[str, Any] | None = None


class SchemaModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    content_type: Literal["artifact"]
    inline: Annotated[str | None, Field(min_length=1)] = None
    artifact_reference: repository_snapshot_reference.Schema
    structured_representation: dict[str, Any] | None = None


class SchemaModel1(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    content_type: Literal["structured_representation"]
    inline: Annotated[str | None, Field(min_length=1)] = None
    artifact_reference: repository_snapshot_reference.Schema | None = None
    structured_representation: dict[str, Any]


class SchemaModel2(RootModel[Schema | SchemaModel | SchemaModel1]):
    root: Annotated[
        Schema | SchemaModel | SchemaModel1,
        Field(
            description="Repository content payload represented inline, by artifact reference, or as a structured representation.",
            title="Kiln repository content",
        ),
    ]
