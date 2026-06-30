"""
Generated Pydantic v2 models for Kiln JSON Schemas.

Do not edit this package by hand. Regenerate with:

    uv run generatemodels
"""

from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field


class Schema(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    elapsed_time: Annotated[float, Field(ge=0.0)]
    files_scanned: Annotated[int, Field(ge=0)]
    candidates_returned: Annotated[int, Field(ge=0)]
    bytes_returned: Annotated[int, Field(ge=0)]
    graph_nodes_visited: Annotated[int, Field(ge=0)]
    representations_generated: Annotated[int | None, Field(ge=0)] = None
    estimated_tokens_returned: Annotated[int, Field(ge=0)]
