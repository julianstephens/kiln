"""
Generated Pydantic v2 models for Kiln JSON Schemas.

Do not edit this package by hand. Regenerate with:

    uv run generatemodels
"""

from __future__ import annotations

from enum import StrEnum


class Schema(StrEnum):
    run_created = "run.created"
    run_initialization_started = "run.initialization_started"
    run_initialization_completed = "run.initialization_completed"
    run_execution_started = "run.execution_started"
    run_output_production_started = "run.output_production_started"
    run_output_production_completed = "run.output_production_completed"
    run_completed = "run.completed"
    run_failed = "run.failed"
