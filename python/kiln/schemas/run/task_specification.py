"""
Generated Pydantic v2 models for Kiln JSON Schemas.

Do not edit this package by hand. Regenerate with:

    uv run generatemodels
"""

from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, RootModel

from . import task_provenance


class SuccessCriterion(RootModel[str]):
    root: Annotated[str, Field(min_length=1)]


class Constraint(RootModel[str]):
    root: Annotated[str, Field(min_length=1)]


class Target(RootModel[str]):
    root: Annotated[str, Field(min_length=1)]


class IssueReference(RootModel[str]):
    root: Annotated[str, Field(min_length=1)]


class WorkflowReference(RootModel[str]):
    root: Annotated[str, Field(min_length=1)]


class Deliverable(RootModel[str]):
    root: Annotated[str, Field(min_length=1)]


class Schema(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    description: Annotated[str, Field(min_length=1)]
    success_criteria: Annotated[list[SuccessCriterion], Field(min_length=1)]
    constraints: list[Constraint]
    targets: list[Target] | None = None
    issue_references: list[IssueReference] | None = None
    workflow_references: list[WorkflowReference] | None = None
    deliverables: list[Deliverable]
    provenance: task_provenance.Schema
