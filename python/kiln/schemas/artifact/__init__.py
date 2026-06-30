"""
Generated Pydantic v2 models for Kiln JSON Schemas.

Do not edit this package by hand. Regenerate with:

    uv run generatemodels
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, RootModel

from . import (
    answer_reference,
    changed_file_manifest_reference,
    diagnostic_log_reference,
    patch_reference,
    reference,
    report_reference,
    repository_snapshot_reference,
    validation_report_reference,
)


class ArtifactReference(RootModel[reference.Schema]):
    root: reference.Schema


class ArtifactChangedFileManifestReference(
    RootModel[changed_file_manifest_reference.Schema]
):
    root: changed_file_manifest_reference.Schema


class ArtifactDiagnosticLogReference(RootModel[diagnostic_log_reference.Schema]):
    root: diagnostic_log_reference.Schema


class ArtifactPatchReference(RootModel[patch_reference.Schema]):
    root: patch_reference.Schema


class ArtifactReportReference(RootModel[report_reference.Schema]):
    root: report_reference.Schema


class ArtifactRepositorySnapshotReference(
    RootModel[repository_snapshot_reference.Schema]
):
    root: repository_snapshot_reference.Schema


class ArtifactValidationReportReference(RootModel[validation_report_reference.Schema]):
    root: validation_report_reference.Schema


class ArtifactAnswerReference(RootModel[answer_reference.Schema]):
    root: answer_reference.Schema


class KilnArtifactGeneratedPythonModelsBundle(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    artifact_answer_reference: ArtifactAnswerReference | None = None
    artifact_changed_file_manifest_reference: (
        ArtifactChangedFileManifestReference | None
    ) = None
    artifact_diagnostic_log_reference: ArtifactDiagnosticLogReference | None = None
    artifact_patch_reference: ArtifactPatchReference | None = None
    artifact_reference: ArtifactReference | None = None
    artifact_report_reference: ArtifactReportReference | None = None
    artifact_repository_snapshot_reference: (
        ArtifactRepositorySnapshotReference | None
    ) = None
    artifact_validation_report_reference: ArtifactValidationReportReference | None = (
        None
    )
