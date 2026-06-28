"""
Generated Pydantic v2 models for Kiln JSON Schemas.

Do not edit this package by hand. Regenerate with:

    uv run generatemodels
"""

from __future__ import annotations

from typing import Annotated, Any, Literal

from pydantic import AwareDatetime, BaseModel, Field


class Schema(BaseModel):
    protocol_version: Literal["1"]
    request_id: Annotated[str, Field(min_length=1)]
    operation: Annotated[str, Field(min_length=1)]
    payload: dict[str, Any]
    correlation_id: Annotated[str | None, Field(min_length=1)] = None
    deadline: AwareDatetime | None = None


class SchemaModel(Schema):
    operation: Annotated[str | None, Field(min_length=1, pattern="^model\\.")] = None
    run_id: Annotated[str, Field(min_length=1)]
    turn_id: Annotated[str | None, Field(min_length=1)] = None
    operation_id: Annotated[str, Field(min_length=1)]
    capability_grant_id: Annotated[str | None, Field(min_length=1)] = None
    budget_reservation_id: Annotated[str | None, Field(min_length=1)] = None
    model_invocation_id: Annotated[str | None, Field(min_length=1)] = None


class SchemaModel1(Schema):
    operation: Annotated[str | None, Field(min_length=1, pattern="^repository\\.")] = (
        None
    )
    run_id: Annotated[str, Field(min_length=1)]
    session_id: Annotated[str | None, Field(min_length=1)] = None
    capability_grant_id: Annotated[str | None, Field(min_length=1)] = None
    budget_reservation_id: Annotated[str | None, Field(min_length=1)] = None
