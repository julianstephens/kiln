"""
Generated Pydantic v2 models for Kiln JSON Schemas.

Do not edit this package by hand. Regenerate with:

    uv run generatemodels
"""

from __future__ import annotations

from enum import StrEnum
from typing import Annotated, Any

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, RootModel

from . import reference


class PreparationStatus(StrEnum):
    pending = "pending"
    preparing = "preparing"
    prepared = "prepared"
    failed = "failed"


class Schema(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    version_id: Annotated[
        str,
        Field(
            description="The unique identifier for this version of the repository",
            min_length=1,
        ),
    ]
    repository_id: Annotated[
        str,
        Field(
            description="The unique identifier for the repository that this version belongs to",
            min_length=1,
        ),
    ]
    source_revision: Annotated[
        str,
        Field(
            description="The source revision that this version of the repository was created from",
            min_length=1,
        ),
    ]
    snapshot_id: Annotated[
        str | None,
        Field(
            description="The unique identifier for the snapshot that this version of the repository was created from",
            min_length=1,
        ),
    ] = None
    parent_repository_version_id: Annotated[
        str | None,
        Field(
            description="The unique identifier for the parent version of the repository that this version was created from",
            min_length=1,
        ),
    ] = None
    content_digest: Annotated[
        str,
        Field(
            description="The digest of the content of this version of the repository",
            min_length=1,
        ),
    ]
    index_compatibility_metadata: Annotated[
        dict[str, Any],
        Field(
            description="The metadata that describes the compatibility of this version of the repository with the index"
        ),
    ]
    creation_reason: Annotated[
        str,
        Field(
            description="The reason that this version of the repository was created",
            min_length=1,
        ),
    ]
    preparation_status: Annotated[
        PreparationStatus,
        Field(
            description="The status of the preparation of this version of the repository"
        ),
    ]
    created_at: Annotated[
        AwareDatetime,
        Field(
            description="The timestamp when this version of the repository was created"
        ),
    ]


class SchemaModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    version_id: Annotated[
        str,
        Field(
            description="The unique identifier for this version of the repository",
            min_length=1,
        ),
    ]
    repository_id: Annotated[
        str,
        Field(
            description="The unique identifier for the repository that this version belongs to",
            min_length=1,
        ),
    ]
    source_revision: Annotated[
        str | None,
        Field(
            description="The source revision that this version of the repository was created from",
            min_length=1,
        ),
    ] = None
    snapshot_id: Annotated[
        str,
        Field(
            description="The unique identifier for the snapshot that this version of the repository was created from",
            min_length=1,
        ),
    ]
    parent_repository_version_id: Annotated[
        str | None,
        Field(
            description="The unique identifier for the parent version of the repository that this version was created from",
            min_length=1,
        ),
    ] = None
    content_digest: Annotated[
        str,
        Field(
            description="The digest of the content of this version of the repository",
            min_length=1,
        ),
    ]
    index_compatibility_metadata: Annotated[
        dict[str, Any],
        Field(
            description="The metadata that describes the compatibility of this version of the repository with the index"
        ),
    ]
    creation_reason: Annotated[
        str,
        Field(
            description="The reason that this version of the repository was created",
            min_length=1,
        ),
    ]
    preparation_status: Annotated[
        PreparationStatus,
        Field(
            description="The status of the preparation of this version of the repository"
        ),
    ]
    created_at: Annotated[
        AwareDatetime,
        Field(
            description="The timestamp when this version of the repository was created"
        ),
    ]


class SchemaModel1(RootModel[Schema | SchemaModel]):
    root: Annotated[Schema | SchemaModel, Field(title="Kiln repository version")]


class AffectedPath(RootModel[str]):
    root: Annotated[str, Field(min_length=1)]


class InvalidatedEvidenceSetItem(RootModel[str]):
    root: Annotated[str, Field(min_length=1)]


class SchemaModel2(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    version_id: Annotated[
        str | None,
        Field(
            description="The unique identifier for this version of the workspace",
            min_length=1,
        ),
    ] = None
    repository_id: Annotated[
        str | None,
        Field(
            description="The unique identifier for the repository that this version of the workspace is associated with",
            min_length=1,
        ),
    ] = None
    base_repository_version_id: Annotated[
        str | None,
        Field(
            description="The unique identifier for the base version of the repository that this version of the workspace is associated with",
            min_length=1,
        ),
    ] = None
    parent_workspace_version_id: Annotated[
        str | None,
        Field(
            description="The unique identifier for the parent version of the workspace that this version was created from",
            min_length=1,
        ),
    ] = None
    mutation_set: Annotated[
        list[dict[str, Any]] | None,
        Field(
            description="The set of mutations that were applied to create this version of the workspace"
        ),
    ] = None
    affected_paths: Annotated[
        list[AffectedPath] | None,
        Field(
            description="The set of paths that were affected by the mutations that were applied to create this version of the workspace",
            min_length=1,
        ),
    ] = None
    invalidated_evidence_set: Annotated[
        list[InvalidatedEvidenceSetItem] | None,
        Field(
            description="The set of evidence that was invalidated by the mutations that were applied to create this version of the workspace"
        ),
    ] = None
    invalidation_reference: Annotated[
        reference.Schema | None,
        Field(
            description="The reference to the evidence that invalidated this version of the workspace"
        ),
    ] = None
    synchronized: Annotated[
        bool | None,
        Field(
            description="Whether this version of the workspace has been synchronized with the base repository version"
        ),
    ] = None
    created_at: Annotated[
        AwareDatetime | None,
        Field(
            description="The timestamp when this version of the workspace was created"
        ),
    ] = None
