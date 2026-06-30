"""
Generated Pydantic v2 models for Kiln JSON Schemas.

Do not edit this package by hand. Regenerate with:

    uv run generatemodels
"""

from __future__ import annotations

from typing import Literal

from .reference import Schema as Schema_1


class Schema(Schema_1):
    artifact_kind: Literal["answer"] | None = None
