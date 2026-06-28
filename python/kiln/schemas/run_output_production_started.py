"""
Generated Pydantic v2 models for Kiln JSON Schemas.

Do not edit this package by hand. Regenerate with:

    uv run generatemodels
"""

from __future__ import annotations

from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

from . import output_mode as output_mode_1


class ExpectedArtifactKind(StrEnum):
    answer = "answer"
    patch = "patch"
    report = "report"
    changed_file_manifest = "changed_file_manifest"
    validation_report = "validation_report"


class Schema(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    completion_proposal_id: Annotated[
        str,
        Field(
            description="The proposal that is being used to produce the output for this run",
            min_length=1,
        ),
    ]
    output_mode: Annotated[
        output_mode_1.Schema,
        Field(
            description="The output mode that is being used to produce the output for this run"
        ),
    ]
    expected_artifact_kinds: Annotated[
        list[ExpectedArtifactKind],
        Field(
            description="The artifact kinds that are expected to be produced by this run",
            min_length=1,
        ),
    ]
