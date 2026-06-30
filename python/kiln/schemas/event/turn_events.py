"""
Generated Pydantic v2 models for Kiln JSON Schemas.

Do not edit this package by hand. Regenerate with:

    uv run generatemodels
"""

from __future__ import annotations

from enum import StrEnum


class Schema(StrEnum):
    turn_started = "turn.started"
    turn_completed = "turn.completed"
    turn_failed = "turn.failed"
