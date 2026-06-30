"""
Generated Pydantic v2 models for Kiln JSON Schemas.

Do not edit this package by hand. Regenerate with:

    uv run generatemodels
"""

from __future__ import annotations

from enum import StrEnum
from typing import Annotated

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, RootModel


class SourceContentId(RootModel[str]):
    root: Annotated[str, Field(min_length=1)]


class CreationMethod(StrEnum):
    generated = "generated"
    extracted = "extracted"


class Schema(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    source_operation_id: Annotated[str, Field(min_length=1)]
    query_id: Annotated[str, Field(min_length=1)]
    extraction_method: Annotated[str, Field(min_length=1)]
    generation_method: Annotated[str | None, Field(min_length=1)] = None
    parser_version: Annotated[str, Field(min_length=1)]
    summarizer_version: Annotated[str | None, Field(min_length=1)] = None
    source_content_ids: list[SourceContentId]
    created_at: AwareDatetime
    creation_method: CreationMethod


class SchemaModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    source_operation_id: Annotated[str, Field(min_length=1)]
    query_id: Annotated[str, Field(min_length=1)]
    extraction_method: Annotated[str | None, Field(min_length=1)] = None
    generation_method: Annotated[str, Field(min_length=1)]
    parser_version: Annotated[str | None, Field(min_length=1)] = None
    summarizer_version: Annotated[str, Field(min_length=1)]
    source_content_ids: list[SourceContentId]
    created_at: AwareDatetime
    creation_method: CreationMethod


class SchemaModel1(RootModel[Schema | SchemaModel]):
    root: Annotated[
        Schema | SchemaModel,
        Field(
            description="Provenance metadata describing how repository content or representations were extracted or generated.",
            title="Kiln repository provenance",
        ),
    ]
