"""
Generated Pydantic v2 models for Kiln JSON Schemas.

Do not edit this package by hand. Regenerate with:

    uv run generatemodels
"""

from __future__ import annotations

from typing import Literal

from . import generate_payload
from .protocol_request import SchemaModel


class Schema(SchemaModel):
    operation: Literal["model.generate"] | None = None
    payload: generate_payload.SchemaModel1 | None = None
