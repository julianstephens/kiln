"""
Generated Pydantic v2 models for Kiln JSON Schemas.

Do not edit this package by hand. Regenerate with:

    uv run generatemodels
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import AwareDatetime, ConfigDict

from . import search_request_payload
from .protocol_request import SchemaModel1


class Schema(SchemaModel1):
    model_config = ConfigDict(
        extra="forbid",
    )
    operation: Literal["repository.search"] | None = None
    payload: search_request_payload.Schema | None = None
    run_id: Any
    session_id: Any
    deadline: AwareDatetime
