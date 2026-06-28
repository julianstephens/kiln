"""
Generated Pydantic v2 models for Kiln JSON Schemas.

Do not edit this package by hand. Regenerate with:

    uv run generatemodels
"""

from __future__ import annotations

from typing import Literal

from . import generate_result
from .protocol_response import SchemaModel1


class Schema(SchemaModel1):
    operation: Literal["model.generate"] | None = None
    status: Literal["ok"] | None = None
    result: generate_result.SchemaModel3
