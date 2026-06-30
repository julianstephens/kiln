"""
Generated Pydantic v2 models for Kiln JSON Schemas.

Do not edit this package by hand. Regenerate with:

    uv run generatemodels
"""

from __future__ import annotations

from enum import StrEnum
from typing import Annotated

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, RootModel

from . import identifier


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


class Effect(StrEnum):
    allow = "allow"
    deny = "deny"


class TimeRange(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    start_time: AwareDatetime
    end_time: AwareDatetime


class Conditions(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    time_range: TimeRange | None = None
    approval_required: bool | None = None
    max_token_usage_count: Annotated[int | None, Field(ge=1)] = None


class Rule(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    rule_id: Annotated[str, Field(min_length=1)]
    effect: Effect
    priority: Annotated[int, Field(ge=0)]
    capability: Annotated[str, Field(min_length=1)]
    scope: Schema_2
    conditions: Conditions | None = None


class KilnCapabilityGeneratedPythonModelsBundle(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    capability_decision: CapabilityDecision | None = None
    capability_grant: CapabilityGrant | None = None
    capability_scope: CapabilityScope | None = None
    capability_security_profile: CapabilitySecurityProfile | None = None


class Decision(StrEnum):
    granted = "granted"
    denied = "denied"


class Schema(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    decision: Annotated[
        Decision,
        Field(description="The decision that was made for this capability request"),
    ]
    grant: Annotated[
        Schema_1,
        Field(description="The grant that was issued for this capability request"),
    ]
    reason: Annotated[
        str,
        Field(
            description="The reason that this capability request was granted or denied",
            min_length=1,
        ),
    ]


class CapabilityDecision(RootModel[Schema]):
    root: Schema


class CapabilityType(StrEnum):
    tool = "tool"
    workflow = "workflow"
    resource = "resource"
    policy = "policy"
    credential = "credential"
    integration = "integration"


class AllowedOperation_1(RootModel[str]):
    root: Annotated[str, Field(min_length=1)]


class CreationSource(StrEnum):
    system = "system"
    user = "user"
    policy = "policy"
    migration = "migration"
    import_ = "import"


class ApprovalMetadata(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    approval_required: bool
    approved_by: Annotated[str | None, Field(min_length=1)] = None
    approved_at: AwareDatetime | None = None
    approval_reference: Annotated[str | None, Field(min_length=1)] = None


class Schema_1(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    grant_id: Annotated[str, Field(min_length=1)]
    capability_type: CapabilityType
    run_id: Annotated[str, Field(min_length=1)]
    capability_scope: Schema_2
    allowed_operations: list[AllowedOperation_1]
    creation_source: CreationSource
    approval_metadata: ApprovalMetadata
    starts_at: AwareDatetime
    expires_at: AwareDatetime
    revoked: bool


class CapabilityGrant(RootModel[Schema_1]):
    root: Schema_1


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


class AllowedOperation_2(StrEnum):
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
        list[AllowedOperation_2] | None, Field(min_length=1)
    ] = None
    artifact_kinds: Annotated[list[ArtifactKind] | None, Field(min_length=1)] = None


class ValidationModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    execution_ids: Annotated[list[ExecutionId] | None, Field(min_length=1)] = None
    validator_kinds: Annotated[list[ValidatorKind], Field(min_length=1)]
    allowed_operations: Annotated[
        list[AllowedOperation_2] | None, Field(min_length=1)
    ] = None
    artifact_kinds: Annotated[list[ArtifactKind] | None, Field(min_length=1)] = None


class ValidationModel1(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    execution_ids: Annotated[list[ExecutionId] | None, Field(min_length=1)] = None
    validator_kinds: Annotated[list[ValidatorKind] | None, Field(min_length=1)] = None
    allowed_operations: Annotated[list[AllowedOperation_2], Field(min_length=1)]
    artifact_kinds: Annotated[list[ArtifactKind] | None, Field(min_length=1)] = None


class ValidationModel2(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    execution_ids: Annotated[list[ExecutionId] | None, Field(min_length=1)] = None
    validator_kinds: Annotated[list[ValidatorKind] | None, Field(min_length=1)] = None
    allowed_operations: Annotated[
        list[AllowedOperation_2] | None, Field(min_length=1)
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


class Schema_2(BaseModel):
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


class CapabilityScope(RootModel[Schema_2]):
    root: Schema_2


class DefaultDenySettings(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    filesystem_read: bool | None = None
    filesystem_write: bool | None = None
    process_execution: bool | None = None
    network_access: bool | None = None
    model_egress: bool | None = None
    external_integration_access: bool | None = None
    artifact_access: bool | None = None
    validation_access: bool | None = None


class Schema_3(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    filesystem_read_scopes: Annotated[list[Schema_2] | None, Field(min_length=1)] = None
    filesystem_write_scopes: Annotated[list[Schema_2] | None, Field(min_length=1)] = (
        None
    )
    process_execution_rules: Annotated[list[Rule] | None, Field(min_length=1)] = None
    network_rules: Annotated[list[Rule] | None, Field(min_length=1)] = None
    model_egress_rules: Annotated[list[Rule] | None, Field(min_length=1)] = None
    external_integration_rules: Annotated[list[Rule] | None, Field(min_length=1)] = None
    artifact_access_rules: Annotated[list[Rule] | None, Field(min_length=1)] = None
    validation_rules: Annotated[list[Rule] | None, Field(min_length=1)] = None
    default_deny_settings: DefaultDenySettings


class SchemaModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    filesystem_read_scopes: Annotated[list[Schema_2], Field(min_length=1)]
    filesystem_write_scopes: Annotated[list[Schema_2] | None, Field(min_length=1)] = (
        None
    )
    process_execution_rules: Annotated[list[Rule] | None, Field(min_length=1)] = None
    network_rules: Annotated[list[Rule] | None, Field(min_length=1)] = None
    model_egress_rules: Annotated[list[Rule] | None, Field(min_length=1)] = None
    external_integration_rules: Annotated[list[Rule] | None, Field(min_length=1)] = None
    artifact_access_rules: Annotated[list[Rule] | None, Field(min_length=1)] = None
    validation_rules: Annotated[list[Rule] | None, Field(min_length=1)] = None
    default_deny_settings: DefaultDenySettings | None = None


class SchemaModel1(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    filesystem_read_scopes: Annotated[list[Schema_2] | None, Field(min_length=1)] = None
    filesystem_write_scopes: Annotated[list[Schema_2], Field(min_length=1)]
    process_execution_rules: Annotated[list[Rule] | None, Field(min_length=1)] = None
    network_rules: Annotated[list[Rule] | None, Field(min_length=1)] = None
    model_egress_rules: Annotated[list[Rule] | None, Field(min_length=1)] = None
    external_integration_rules: Annotated[list[Rule] | None, Field(min_length=1)] = None
    artifact_access_rules: Annotated[list[Rule] | None, Field(min_length=1)] = None
    validation_rules: Annotated[list[Rule] | None, Field(min_length=1)] = None
    default_deny_settings: DefaultDenySettings | None = None


class SchemaModel2(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    filesystem_read_scopes: Annotated[list[Schema_2] | None, Field(min_length=1)] = None
    filesystem_write_scopes: Annotated[list[Schema_2] | None, Field(min_length=1)] = (
        None
    )
    process_execution_rules: Annotated[list[Rule], Field(min_length=1)]
    network_rules: Annotated[list[Rule] | None, Field(min_length=1)] = None
    model_egress_rules: Annotated[list[Rule] | None, Field(min_length=1)] = None
    external_integration_rules: Annotated[list[Rule] | None, Field(min_length=1)] = None
    artifact_access_rules: Annotated[list[Rule] | None, Field(min_length=1)] = None
    validation_rules: Annotated[list[Rule] | None, Field(min_length=1)] = None
    default_deny_settings: DefaultDenySettings | None = None


class SchemaModel3(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    filesystem_read_scopes: Annotated[list[Schema_2] | None, Field(min_length=1)] = None
    filesystem_write_scopes: Annotated[list[Schema_2] | None, Field(min_length=1)] = (
        None
    )
    process_execution_rules: Annotated[list[Rule] | None, Field(min_length=1)] = None
    network_rules: Annotated[list[Rule], Field(min_length=1)]
    model_egress_rules: Annotated[list[Rule] | None, Field(min_length=1)] = None
    external_integration_rules: Annotated[list[Rule] | None, Field(min_length=1)] = None
    artifact_access_rules: Annotated[list[Rule] | None, Field(min_length=1)] = None
    validation_rules: Annotated[list[Rule] | None, Field(min_length=1)] = None
    default_deny_settings: DefaultDenySettings | None = None


class SchemaModel4(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    filesystem_read_scopes: Annotated[list[Schema_2] | None, Field(min_length=1)] = None
    filesystem_write_scopes: Annotated[list[Schema_2] | None, Field(min_length=1)] = (
        None
    )
    process_execution_rules: Annotated[list[Rule] | None, Field(min_length=1)] = None
    network_rules: Annotated[list[Rule] | None, Field(min_length=1)] = None
    model_egress_rules: Annotated[list[Rule], Field(min_length=1)]
    external_integration_rules: Annotated[list[Rule] | None, Field(min_length=1)] = None
    artifact_access_rules: Annotated[list[Rule] | None, Field(min_length=1)] = None
    validation_rules: Annotated[list[Rule] | None, Field(min_length=1)] = None
    default_deny_settings: DefaultDenySettings | None = None


class SchemaModel5(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    filesystem_read_scopes: Annotated[list[Schema_2] | None, Field(min_length=1)] = None
    filesystem_write_scopes: Annotated[list[Schema_2] | None, Field(min_length=1)] = (
        None
    )
    process_execution_rules: Annotated[list[Rule] | None, Field(min_length=1)] = None
    network_rules: Annotated[list[Rule] | None, Field(min_length=1)] = None
    model_egress_rules: Annotated[list[Rule] | None, Field(min_length=1)] = None
    external_integration_rules: Annotated[list[Rule], Field(min_length=1)]
    artifact_access_rules: Annotated[list[Rule] | None, Field(min_length=1)] = None
    validation_rules: Annotated[list[Rule] | None, Field(min_length=1)] = None
    default_deny_settings: DefaultDenySettings | None = None


class SchemaModel6(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    filesystem_read_scopes: Annotated[list[Schema_2] | None, Field(min_length=1)] = None
    filesystem_write_scopes: Annotated[list[Schema_2] | None, Field(min_length=1)] = (
        None
    )
    process_execution_rules: Annotated[list[Rule] | None, Field(min_length=1)] = None
    network_rules: Annotated[list[Rule] | None, Field(min_length=1)] = None
    model_egress_rules: Annotated[list[Rule] | None, Field(min_length=1)] = None
    external_integration_rules: Annotated[list[Rule] | None, Field(min_length=1)] = None
    artifact_access_rules: Annotated[list[Rule], Field(min_length=1)]
    validation_rules: Annotated[list[Rule] | None, Field(min_length=1)] = None
    default_deny_settings: DefaultDenySettings | None = None


class SchemaModel7(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    filesystem_read_scopes: Annotated[list[Schema_2] | None, Field(min_length=1)] = None
    filesystem_write_scopes: Annotated[list[Schema_2] | None, Field(min_length=1)] = (
        None
    )
    process_execution_rules: Annotated[list[Rule] | None, Field(min_length=1)] = None
    network_rules: Annotated[list[Rule] | None, Field(min_length=1)] = None
    model_egress_rules: Annotated[list[Rule] | None, Field(min_length=1)] = None
    external_integration_rules: Annotated[list[Rule] | None, Field(min_length=1)] = None
    artifact_access_rules: Annotated[list[Rule] | None, Field(min_length=1)] = None
    validation_rules: Annotated[list[Rule], Field(min_length=1)]
    default_deny_settings: DefaultDenySettings | None = None


class SchemaModel8(
    RootModel[
        Schema_3
        | SchemaModel
        | SchemaModel1
        | SchemaModel2
        | SchemaModel3
        | SchemaModel4
        | SchemaModel5
        | SchemaModel6
        | SchemaModel7
    ]
):
    root: Annotated[
        Schema_3
        | SchemaModel
        | SchemaModel1
        | SchemaModel2
        | SchemaModel3
        | SchemaModel4
        | SchemaModel5
        | SchemaModel6
        | SchemaModel7,
        Field(title="Kiln capability security profile"),
    ]


class CapabilitySecurityProfile(RootModel[SchemaModel8]):
    root: SchemaModel8
