"""
Generated Pydantic v2 models for Kiln JSON Schemas.

Do not edit this package by hand. Regenerate with:

    uv run generatemodels
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, RootModel

from . import byte_range, source_range


class CommonByteRange(RootModel[byte_range.Schema]):
    root: byte_range.Schema


class CommonSourceRange(RootModel[source_range.Schema]):
    root: source_range.Schema


class KilnCommonGeneratedPythonModelsBundle(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    common_byte_range: CommonByteRange | None = None
    common_source_range: CommonSourceRange | None = None
