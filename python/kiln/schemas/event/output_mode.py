"""
Generated Pydantic v2 models for Kiln JSON Schemas.

Do not edit this package by hand. Regenerate with:

    uv run generatemodels
"""

from __future__ import annotations

from enum import StrEnum


class Schema(StrEnum):
    answer = "answer"
    patch = "patch"
    answer_with_patch = "answer_with_patch"
    report = "report"
