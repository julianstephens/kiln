"""
Generated Pydantic v2 models for Kiln JSON Schemas.

Do not edit this package by hand. Regenerate with:

    uv run generatemodels
"""

from __future__ import annotations

from enum import StrEnum
from typing import Annotated

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field

from . import reference


class CreationReason(StrEnum):
    model_request_rendered = "model_request_rendered"
    model_response_received = "model_response_received"
    candidate_batch_materialized = "candidate_batch_materialized"
    final_result_bundle_created = "final_result_bundle_created"
    output_production = "output_production"
    validation = "validation"
    diagnostic = "diagnostic"
    repository_snapshot = "repository_snapshot"
    other = "other"


class CreatedBy(StrEnum):
    runtime = "runtime"
    context_renderer = "context_renderer"
    model_adapter = "model_adapter"
    model_interpreter = "model_interpreter"
    repository_worker = "repository_worker"
    artifact_store = "artifact_store"
    output_producer = "output_producer"
    validator = "validator"
    test_harness = "test_harness"
    unknown = "unknown"


class CandidateKind(StrEnum):
    answer = "answer"
    patch = "patch"
    report = "report"
    tool_call = "tool_call"
    validation_judgment = "validation_judgment"
    mixed = "mixed"


class BundleKind(StrEnum):
    answer = "answer"
    patch = "patch"
    answer_with_patch = "answer_with_patch"
    report = "report"
    failed = "failed"
    canceled = "canceled"
    exhausted = "exhausted"


class ArtifactMetadata(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    model_invocation_id: Annotated[str | None, Field(min_length=1)] = None
    render_id: Annotated[str | None, Field(min_length=1)] = None
    candidate_batch_id: Annotated[str | None, Field(min_length=1)] = None
    final_result_bundle_id: Annotated[str | None, Field(min_length=1)] = None
    candidate_count: Annotated[int | None, Field(ge=0)] = None
    candidate_kind: CandidateKind | None = None
    bundle_kind: BundleKind | None = None
    contains_sensitive_content: bool | None = None
    redacted: bool | None = None


class Schema(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    artifact: Annotated[
        reference.Schema,
        Field(description="Reference to the artifact that was created."),
    ]
    creation_reason: Annotated[
        CreationReason, Field(description="Reason this artifact was created.")
    ]
    created_by: Annotated[
        CreatedBy, Field(description="Logical component that created the artifact.")
    ]
    producer_operation_id: Annotated[
        str | None,
        Field(
            description="Operation that produced the artifact, when applicable.",
            min_length=1,
        ),
    ] = None
    source_artifact_references: Annotated[
        list[reference.Schema] | None,
        Field(
            description="Artifacts used as inputs to create this artifact.",
            min_length=1,
        ),
    ] = None
    artifact_metadata: Annotated[
        ArtifactMetadata | None,
        Field(description="Kind-specific artifact creation metadata."),
    ] = None
    created_at: Annotated[
        AwareDatetime, Field(description="When the artifact was created.")
    ]
