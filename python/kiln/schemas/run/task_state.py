"""
Generated Pydantic v2 models for Kiln JSON Schemas.

Do not edit this package by hand. Regenerate with:

    uv run generatemodels
"""

from __future__ import annotations

from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, RootModel

from . import source_range


class CompletedStep(RootModel[str]):
    root: Annotated[str, Field(min_length=1)]


class UnresolvedQuestion(RootModel[str]):
    root: Annotated[str, Field(min_length=1)]


class Hypothes(RootModel[str]):
    root: Annotated[str, Field(min_length=1)]


class Action(StrEnum):
    add = "add"
    delete = "delete"


class KnownFailure(RootModel[str]):
    root: Annotated[str, Field(min_length=1)]


class CompletionEvidenceItem(RootModel[str]):
    root: Annotated[str, Field(min_length=1)]


class ProposedChange(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    action: Action
    target_range: source_range.Schema
    content: Annotated[str | None, Field(min_length=1)] = None


class Schema(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    current_objective: Annotated[str, Field(min_length=1)]
    current_plan: Annotated[str, Field(min_length=1)]
    completed_steps: list[CompletedStep]
    unresolved_questions: list[UnresolvedQuestion]
    hypotheses: list[Hypothes]
    proposed_changes: list[ProposedChange] | None = None
    known_failures: list[KnownFailure] | None = None
    completion_evidence: list[CompletionEvidenceItem]
    state_revision: Annotated[str, Field(min_length=1)]
