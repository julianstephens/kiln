"""
Generated Pydantic v2 models for Kiln JSON Schemas.

Do not edit this package by hand. Regenerate with:

    uv run generatemodels
"""

from __future__ import annotations

from enum import StrEnum


class Schema(StrEnum):
    model_request_rendered = "model.request_rendered"
    model_egress_evaluated = "model.egress_evaluated"
    model_invocation_started = "model.invocation_started"
    model_invocation_completed = "model.invocation_completed"
    model_invocation_failed = "model.invocation_failed"
    model_response_interpreted = "model.response_interpreted"
