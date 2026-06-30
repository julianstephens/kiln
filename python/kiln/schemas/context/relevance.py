"""
Generated Pydantic v2 models for Kiln JSON Schemas.

Do not edit this package by hand. Regenerate with:

    uv run generatemodels
"""

from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, RootModel


class MatchTerm(RootModel[str]):
    root: Annotated[str, Field(min_length=1)]


class Schema(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    lexical_score: Annotated[int, Field(ge=0)]
    semantic_score: Annotated[int, Field(ge=0)]
    hybrid_score: Annotated[int, Field(ge=0)]
    graph_distance: Annotated[int, Field(ge=0)]
    match_terms: list[MatchTerm]
    rank: Annotated[int, Field(ge=1)]
    score_explanation: Annotated[str, Field(min_length=1)]
