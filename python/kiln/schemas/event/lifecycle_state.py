"""
Generated Pydantic v2 models for Kiln JSON Schemas.

Do not edit this package by hand. Regenerate with:

    uv run generatemodels
"""

from __future__ import annotations

from enum import StrEnum


class Schema(StrEnum):
    created = "created"
    initializing = "initializing"
    preparing_repository = "preparing_repository"
    running = "running"
    producing_output = "producing_output"
    validating = "validating"
    completed = "completed"
    failed = "failed"
    canceled = "canceled"
    exhausted = "exhausted"
