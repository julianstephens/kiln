"""
Generated Pydantic v2 models for Kiln JSON Schemas.

Do not edit this package by hand. Regenerate with:

    uv run generatemodels
"""

from __future__ import annotations

from enum import StrEnum
from typing import Annotated, Any

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field


class Scope(StrEnum):
    installation = "installation"
    tenant = "tenant"


class ArtifactKind(StrEnum):
    answer = "answer"
    changed_file_manifest = "changed_file_manifest"
    diagnostic_log = "diagnostic_log"
    patch = "patch"
    repository_snapshot = "repository_snapshot"
    validation_report = "validation_report"
    model_request = "model_request"
    model_response = "model_response"
    candidate_batch = "candidate_batch"
    final_result_bundle = "final_result_bundle"


class Schema(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    artifact_id: Annotated[str, Field(min_length=1)]
    scope: Scope
    run_id: Annotated[str | None, Field(min_length=1)] = None
    artifact_kind: ArtifactKind
    content_type: Annotated[str, Field(min_length=1)]
    content_hash: Annotated[str, Field(min_length=1)]
    uncompressed_size: Annotated[int, Field(ge=0)]
    stored_size: Annotated[int, Field(ge=0)]
    compression_method: Annotated[str, Field(min_length=1)]
    retention_class: Annotated[str, Field(min_length=1)]
    created_at: AwareDatetime
    encryption_metadata: dict[str, Any] | None = None
