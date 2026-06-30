"""
Generated Pydantic v2 models for Kiln JSON Schemas.

Do not edit this package by hand. Regenerate with:

    uv run generatemodels
"""

from __future__ import annotations

from enum import StrEnum
from typing import Annotated, Any

from pydantic import BaseModel, ConfigDict, Field, RootModel

from . import (
    approval_requirement,
    citation_requirement,
    identifier,
    limits,
    policy_requirement,
    schema_requirement,
)


class DestinationType(StrEnum):
    host = "host"
    domain_suffix = "domain_suffix"
    url_origin = "url_origin"
    cidr = "cidr"
    private_network = "private_network"
    loopback = "loopback"
    link_local = "link_local"
    metadata_service = "metadata_service"
    external_integration = "external_integration"


class Port(RootModel[int]):
    root: Annotated[int, Field(ge=1, le=65535)]


class Protocol(StrEnum):
    http = "http"
    https = "https"
    ssh = "ssh"
    git = "git"
    grpc = "grpc"


class Purpose(StrEnum):
    model_inference = "model_inference"
    repository_metadata = "repository_metadata"
    repository_fetch = "repository_fetch"
    package_metadata = "package_metadata"
    artifact_storage = "artifact_storage"
    validation = "validation"
    telemetry = "telemetry"


class NetworkDestination(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    destination_type: DestinationType
    host: Annotated[str | None, Field(min_length=1)] = None
    domain_suffix: Annotated[str | None, Field(pattern="^\\.[A-Za-z0-9.-]+$")] = None
    url_origin: str | None = None
    cidr: Annotated[str | None, Field(min_length=1)] = None
    external_integration_id: Annotated[str | None, Field(min_length=1)] = None
    ports: Annotated[list[Port] | None, Field(min_length=1)] = None
    protocols: Annotated[list[Protocol] | None, Field(min_length=1)] = None
    purposes: Annotated[list[Purpose] | None, Field(min_length=1)] = None
    reason: Annotated[str | None, Field(min_length=1)] = None


class IntegrationKind(StrEnum):
    model_provider = "model_provider"
    artifact_store = "artifact_store"
    repository_provider = "repository_provider"
    validation_service = "validation_service"


class AllowedOperation(StrEnum):
    generate = "generate"
    read = "read"
    write = "write"
    read_metadata = "read_metadata"
    read_content = "read_content"
    validate = "validate"


class ExternalIntegration(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    integration_kind: IntegrationKind
    integration_id: Annotated[str, Field(min_length=1)]
    allowed_operations: Annotated[list[AllowedOperation], Field(min_length=1)]


class ValidationApprovalRequirement(RootModel[approval_requirement.Schema]):
    root: approval_requirement.Schema


class ValidationCitationRequirement(RootModel[citation_requirement.Schema]):
    root: citation_requirement.Schema


class ValidationPolicyRequirement(RootModel[policy_requirement.Schema]):
    root: policy_requirement.Schema


class ValidationSchemaRequirement(RootModel[schema_requirement.Schema]):
    root: schema_requirement.Schema


class KilnValidationGeneratedPythonModelsBundle(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    validation_approval_requirement: ValidationApprovalRequirement | None = None
    validation_citation_requirement: ValidationCitationRequirement | None = None
    validation_policy_requirement: ValidationPolicyRequirement | None = None
    validation_requirement: ValidationRequirement | None = None
    validation_schema_requirement: ValidationSchemaRequirement | None = None


class RequirementKind(StrEnum):
    schema = "schema"
    policy = "policy"
    approval = "approval"
    citation = "citation"


class Severity(StrEnum):
    advisory = "advisory"
    blocking = "blocking"


class Trigger(StrEnum):
    before_model = "before_model"
    after_model = "after_model"
    before_output = "before_output"
    before_publication = "before_publication"
    on_demand = "on_demand"


class CapabilityRequirement(RootModel[str]):
    root: Annotated[str, Field(min_length=1)]


class Schema(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    requirement_id: Annotated[str, Field(min_length=1)]
    requirement_kind: RequirementKind
    severity: Severity
    trigger: Trigger
    scope: Schema_1 | None = None
    budget_limits: limits.Schema | None = None
    capability_requirements: Annotated[
        list[CapabilityRequirement] | None, Field(min_length=1)
    ] = None
    config: dict[str, Any]


class ValidationRequirement(RootModel[Schema]):
    root: Schema


class Id(RootModel[str]):
    root: Annotated[str, Field(min_length=1)]


class Kind(RootModel[str]):
    root: Annotated[str, Field(min_length=1)]


class Ownership(StrEnum):
    current_run = "current_run"
    current_repository_session = "current_repository_session"
    current_workspace = "current_workspace"
    installation = "installation"


class RetentionClass(StrEnum):
    temporary = "temporary"
    standard = "standard"
    audit = "audit"
    debug = "debug"


class Artifacts(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    ids: Annotated[list[Id], Field(min_length=1)]
    kinds: Annotated[list[Kind] | None, Field(min_length=1)] = None
    ownership: Ownership | None = None
    retention_classes: Annotated[list[RetentionClass] | None, Field(min_length=1)] = (
        None
    )


class ArtifactsModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    ids: Annotated[list[Id] | None, Field(min_length=1)] = None
    kinds: Annotated[list[Kind], Field(min_length=1)]
    ownership: Ownership | None = None
    retention_classes: Annotated[list[RetentionClass] | None, Field(min_length=1)] = (
        None
    )


class ArtifactsModel1(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    ids: Annotated[list[Id] | None, Field(min_length=1)] = None
    kinds: Annotated[list[Kind] | None, Field(min_length=1)] = None
    ownership: Ownership
    retention_classes: Annotated[list[RetentionClass] | None, Field(min_length=1)] = (
        None
    )


class ArtifactsModel2(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    ids: Annotated[list[Id] | None, Field(min_length=1)] = None
    kinds: Annotated[list[Kind] | None, Field(min_length=1)] = None
    ownership: Ownership | None = None
    retention_classes: Annotated[list[RetentionClass], Field(min_length=1)]


class Path(RootModel[str]):
    root: Annotated[str, Field(min_length=1)]


class Pattern(RootModel[str]):
    root: Annotated[str, Field(min_length=1)]


class Acces(StrEnum):
    read = "read"
    write = "write"
    execute = "execute"


class Filesystem(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    paths: Annotated[list[Path], Field(min_length=1)]
    patterns: Annotated[list[Pattern] | None, Field(min_length=1)] = None
    access: Annotated[list[Acces], Field(min_length=1)]


class FilesystemModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    paths: Annotated[list[Path] | None, Field(min_length=1)] = None
    patterns: Annotated[list[Pattern], Field(min_length=1)]
    access: Annotated[list[Acces], Field(min_length=1)]


class Default(StrEnum):
    deny = "deny"
    allow = "allow"


class ModelId(RootModel[str]):
    root: Annotated[str, Field(min_length=1)]


class OperationKind(RootModel[str]):
    root: Annotated[str, Field(min_length=1)]


class ExecutionId(RootModel[str]):
    root: Annotated[str, Field(min_length=1)]


class ValidatorKind(StrEnum):
    unit_tests = "unit_tests"
    integration_tests = "integration_tests"
    typecheck = "typecheck"
    lint = "lint"
    format_check = "format_check"
    security_scan = "security_scan"
    custom = "custom"


class AllowedOperation_1(StrEnum):
    start = "start"
    cancel = "cancel"
    read_status = "read_status"
    read_report = "read_report"
    write_report = "write_report"
    read_logs = "read_logs"
    write_logs = "write_logs"


class ArtifactKind(StrEnum):
    patch = "patch"
    changed_file_manifest = "changed-file-manifest"
    validation_report = "validation-report"
    diagnostic_log = "diagnostic-log"


class Validation(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    execution_ids: Annotated[list[ExecutionId], Field(min_length=1)]
    validator_kinds: Annotated[list[ValidatorKind] | None, Field(min_length=1)] = None
    allowed_operations: Annotated[
        list[AllowedOperation_1] | None, Field(min_length=1)
    ] = None
    artifact_kinds: Annotated[list[ArtifactKind] | None, Field(min_length=1)] = None


class ValidationModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    execution_ids: Annotated[list[ExecutionId] | None, Field(min_length=1)] = None
    validator_kinds: Annotated[list[ValidatorKind], Field(min_length=1)]
    allowed_operations: Annotated[
        list[AllowedOperation_1] | None, Field(min_length=1)
    ] = None
    artifact_kinds: Annotated[list[ArtifactKind] | None, Field(min_length=1)] = None


class ValidationModel1(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    execution_ids: Annotated[list[ExecutionId] | None, Field(min_length=1)] = None
    validator_kinds: Annotated[list[ValidatorKind] | None, Field(min_length=1)] = None
    allowed_operations: Annotated[list[AllowedOperation_1], Field(min_length=1)]
    artifact_kinds: Annotated[list[ArtifactKind] | None, Field(min_length=1)] = None


class ValidationModel2(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    execution_ids: Annotated[list[ExecutionId] | None, Field(min_length=1)] = None
    validator_kinds: Annotated[list[ValidatorKind] | None, Field(min_length=1)] = None
    allowed_operations: Annotated[
        list[AllowedOperation_1] | None, Field(min_length=1)
    ] = None
    artifact_kinds: Annotated[list[ArtifactKind], Field(min_length=1)]


class NetworkDestinations(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    default: Default
    allow: Annotated[list[NetworkDestination], Field(min_length=1)]
    deny: Annotated[list[NetworkDestination] | None, Field(min_length=1)] = None


class NetworkDestinationsModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    default: Default
    allow: Annotated[list[NetworkDestination] | None, Field(min_length=1)] = None
    deny: Annotated[list[NetworkDestination], Field(min_length=1)]


class Schema_1(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    installation_id: Annotated[str | None, Field(min_length=1)] = None
    tenant_id: Annotated[str | None, Field(min_length=1)] = None
    repository: identifier.Schema | None = None
    run_id: Annotated[str | None, Field(min_length=1)] = None
    repository_session_id: Annotated[str | None, Field(min_length=1)] = None
    artifacts: Artifacts | ArtifactsModel | ArtifactsModel1 | ArtifactsModel2 | None = (
        None
    )
    filesystem: Filesystem | FilesystemModel | None = None
    network_destinations: NetworkDestinations | NetworkDestinationsModel | None = None
    external_integrations: Annotated[
        list[ExternalIntegration] | None, Field(min_length=1)
    ] = None
    model_ids: Annotated[list[ModelId] | None, Field(min_length=1)] = None
    operation_kinds: Annotated[list[OperationKind] | None, Field(min_length=1)] = None
    validation: (
        Validation | ValidationModel | ValidationModel1 | ValidationModel2 | None
    ) = None
