"""
Generated Pydantic v2 models for Kiln JSON Schemas.

Do not edit this package by hand. Regenerate with:

    uv run generatemodels
"""

from __future__ import annotations

from enum import StrEnum


class Schema(StrEnum):
    validation = "validation"
    capability = "capability"
    repository = "repository"
    tool = "tool"
    external_operation = "external_operation"
    output_production = "output_production"
    runtime = "runtime"
    internal = "internal"
