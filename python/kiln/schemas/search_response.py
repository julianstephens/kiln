"""
Generated Pydantic v2 models for Kiln JSON Schemas.

Do not edit this package by hand. Regenerate with:

    uv run generatemodels
"""

from __future__ import annotations

from typing import Literal

from pydantic import ConfigDict

from . import search_result
from .protocol_response import SchemaModel


class Schema(SchemaModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    operation: Literal["repository.search"] | None = None
    status: Literal["ok"] | None = None
    result: search_result.Schema
