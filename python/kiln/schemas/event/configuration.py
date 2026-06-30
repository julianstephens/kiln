"""
Generated Pydantic v2 models for Kiln JSON Schemas.

Do not edit this package by hand. Regenerate with:

    uv run generatemodels
"""

from __future__ import annotations

from enum import StrEnum
from typing import Annotated, Any

from pydantic import BaseModel, ConfigDict, Field, RootModel


class ToolCallMode(StrEnum):
    none = "none"
    restricted = "restricted"
    unrestricted = "unrestricted"


class Schema(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    model_id: Annotated[str, Field(min_length=1)]
    context_limit: Annotated[int, Field(ge=1)]
    tool_call_mode: ToolCallMode
    tokenizer_strategy: Annotated[str, Field(min_length=1)]
    generation_parameters: dict[str, Any]
    streaming_preference: Annotated[str, Field(min_length=1)]
    provider_id: Annotated[str, Field(min_length=1)]
    local_adapter_id: Annotated[str | None, Field(min_length=1)] = None


class SchemaModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    model_id: Annotated[str, Field(min_length=1)]
    context_limit: Annotated[int, Field(ge=1)]
    tool_call_mode: ToolCallMode
    tokenizer_strategy: Annotated[str, Field(min_length=1)]
    generation_parameters: dict[str, Any]
    streaming_preference: Annotated[str, Field(min_length=1)]
    provider_id: Annotated[str | None, Field(min_length=1)] = None
    local_adapter_id: Annotated[str, Field(min_length=1)]


class SchemaModel1(RootModel[Schema | SchemaModel]):
    root: Annotated[Schema | SchemaModel, Field(title="Kiln model configuration")]
