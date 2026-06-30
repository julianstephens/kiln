"""
Generated Pydantic v2 models for Kiln JSON Schemas.

Do not edit this package by hand. Regenerate with:

    uv run generatemodels
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, RootModel

from . import (
    alternative_representation,
    candidate,
    content,
    cost,
    diagnostic,
    error,
    identifier,
    open_session_request_payload,
    preparation_status,
    provenance,
    relevance,
    search_request_payload,
    search_result,
    session,
    source,
    source_request_payload,
    source_result,
    usage,
    validity,
    version,
)


class RepositoryCost(RootModel[cost.Schema]):
    root: cost.Schema


class RepositoryIdentifier(RootModel[identifier.Schema]):
    root: identifier.Schema


class RepositoryProvenance(RootModel[provenance.SchemaModel1]):
    root: provenance.SchemaModel1


class RepositoryRelevance(RootModel[relevance.Schema]):
    root: relevance.Schema


class RepositoryValidity(RootModel[validity.Schema]):
    root: validity.Schema


class RepositoryAlternativeRepresentation(RootModel[alternative_representation.Schema]):
    root: alternative_representation.Schema


class RepositoryDiagnostic(RootModel[diagnostic.Schema]):
    root: diagnostic.Schema


class RepositoryOpenSessionRequestPayload(
    RootModel[open_session_request_payload.Schema]
):
    root: open_session_request_payload.Schema


class RepositoryPreparationStatus(RootModel[preparation_status.Schema]):
    root: preparation_status.Schema


class RepositorySearchRequestPayload(RootModel[search_request_payload.Schema]):
    root: search_request_payload.Schema


class RepositorySession(RootModel[session.Schema]):
    root: session.Schema


class RepositorySource(RootModel[source.Schema]):
    root: source.Schema


class RepositorySourceRequestPayload(RootModel[source_request_payload.Schema]):
    root: source_request_payload.Schema


class RepositoryUsage(RootModel[usage.Schema]):
    root: usage.Schema


class RepositoryVersion(RootModel[version.SchemaModel1]):
    root: version.SchemaModel1


class RepositoryContent(RootModel[content.SchemaModel2]):
    root: content.SchemaModel2


class RepositoryError(RootModel[error.Schema]):
    root: error.Schema


class RepositoryCandidate(RootModel[candidate.Schema]):
    root: candidate.Schema


class RepositorySearchResult(RootModel[search_result.Schema]):
    root: search_result.Schema


class RepositorySourceResult(RootModel[source_result.Schema]):
    root: source_result.Schema


class KilnRepositoryGeneratedPythonModelsBundle(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    repository_alternative_representation: (
        RepositoryAlternativeRepresentation | None
    ) = None
    repository_candidate: RepositoryCandidate | None = None
    repository_content: RepositoryContent | None = None
    repository_cost: RepositoryCost | None = None
    repository_diagnostic: RepositoryDiagnostic | None = None
    repository_error: RepositoryError | None = None
    repository_identifier: RepositoryIdentifier | None = None
    repository_open_session_request_payload: (
        RepositoryOpenSessionRequestPayload | None
    ) = None
    repository_preparation_status: RepositoryPreparationStatus | None = None
    repository_provenance: RepositoryProvenance | None = None
    repository_relevance: RepositoryRelevance | None = None
    repository_search_request_payload: RepositorySearchRequestPayload | None = None
    repository_search_result: RepositorySearchResult | None = None
    repository_session: RepositorySession | None = None
    repository_source: RepositorySource | None = None
    repository_source_request_payload: RepositorySourceRequestPayload | None = None
    repository_source_result: RepositorySourceResult | None = None
    repository_usage: RepositoryUsage | None = None
    repository_validity: RepositoryValidity | None = None
    repository_version: RepositoryVersion | None = None
