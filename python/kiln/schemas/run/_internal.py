"""
Generated Pydantic v2 models for Kiln JSON Schemas.

Do not edit this package by hand. Regenerate with:

    uv run generatemodels
"""

from __future__ import annotations

from enum import StrEnum
from typing import Annotated, Any

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, RootModel

from . import (
    answer_reference,
    changed_file_manifest_reference,
    configuration,
    error_category,
    identifier,
    limits,
    patch_reference,
    reference,
    report_reference,
    task_provenance,
    task_state,
    validation_report_reference,
)
from . import error as error_1
from . import lifecycle_state as lifecycle_state_1
from . import output_mode as output_mode_1
from . import stop_reason as stop_reason_1
from . import task_specification as task_specification_1
from . import terminal_result_reference as terminal_result_reference_1
from . import usage as usage_1


class RunErrorCategory(RootModel[error_category.Schema]):
    root: error_category.Schema


class BudgetDetails(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    configured_limit: Annotated[int, Field(ge=0)]
    reserved_amount: Annotated[int, Field(ge=0)]
    committed_amount: Annotated[int, Field(ge=0)]
    remaining_amount: Annotated[int, Field(ge=0)]
    exhausted: bool


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


class RunStopReason(RootModel[stop_reason_1.Schema]):
    root: stop_reason_1.Schema


class RunTaskProvenance(RootModel[task_provenance.Schema]):
    root: task_provenance.Schema


class RunTerminalResultReference(RootModel[terminal_result_reference_1.Schema]):
    root: terminal_result_reference_1.Schema


class RunLifecycleState(RootModel[lifecycle_state_1.Schema]):
    root: lifecycle_state_1.Schema


class RunOutputMode(RootModel[output_mode_1.Schema]):
    root: output_mode_1.Schema


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


class RunTaskSpecification(RootModel[task_specification_1.Schema]):
    root: task_specification_1.Schema


class RunTaskState(RootModel[task_state.Schema]):
    root: task_state.Schema


class RunError(RootModel[error_1.Schema]):
    root: error_1.Schema


class KilnRunGeneratedPythonModelsBundle(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    run_error: RunError | None = None
    run_error_category: RunErrorCategory | None = None
    run_lifecycle_state: RunLifecycleState | None = None
    run_output_mode: RunOutputMode | None = None
    run_result: RunResult | None = None
    run_specification: RunSpecification | None = None
    run_state: RunState | None = None
    run_stop_reason: RunStopReason | None = None
    run_task_provenance: RunTaskProvenance | None = None
    run_task_specification: RunTaskSpecification | None = None
    run_task_state: RunTaskState | None = None
    run_terminal_result_reference: RunTerminalResultReference | None = None


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
    scope: Schema_2 | None = None
    budget_limits: limits.Schema | None = None
    capability_requirements: Annotated[
        list[CapabilityRequirement] | None, Field(min_length=1)
    ] = None
    config: dict[str, Any]


class TerminalStatus(StrEnum):
    completed = "completed"
    failed = "failed"
    canceled = "canceled"
    exhausted = "exhausted"


class ContentType(StrEnum):
    text_plain = "text/plain"
    text_markdown = "text/markdown"
    application_json = "application/json"


class Answer(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    content_type: ContentType
    content: Annotated[str, Field(min_length=1)]


class EventStreamRange(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    first_sequence: Annotated[int, Field(ge=0)]
    last_sequence: Annotated[int, Field(ge=0)]


class Budget(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    usage: usage_1.Schema
    state: SchemaModel_1 | None = None


class Schema_1(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    run_id: Annotated[str, Field(min_length=1)]
    terminal_status: TerminalStatus
    stop_reason: stop_reason_1.Schema
    output_mode: output_mode_1.Schema
    error: error_1.Schema | None = None
    answer: Answer | None = None
    answer_artifact: answer_reference.Schema | None = None
    report_artifact: report_reference.Schema | None = None
    patch_artifact: patch_reference.Schema | None = None
    changed_file_manifest_artifact: changed_file_manifest_reference.Schema | None = None
    validation_report_artifact: validation_report_reference.Schema | None = None
    budget: Budget
    event_stream_range: EventStreamRange | None = None
    event_stream_reference: Annotated[str | None, Field(min_length=1)] = None
    context_ledger_reference: Annotated[str, Field(min_length=1)]
    additional_artifact_references: list[reference.Schema] | None = None


class RunResult(RootModel[Schema_1]):
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


class OutputMode(StrEnum):
    answer = "answer"
    patch = "patch"
    answer_with_patch = "answer_with_patch"
    report = "report"


class Validation_1(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    profile_id: Annotated[str | None, Field(min_length=1)] = None
    requirements: Annotated[list[Schema] | None, Field(min_length=1)] = None


class Schema_4(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    repository: identifier.Schema
    task_specification: task_specification_1.Schema
    model_configuration: configuration.SchemaModel1
    budget_limits: limits.Schema
    security_profile: SchemaModel8
    validation: Validation_1 | None = None
    output_mode: OutputMode
    caller_metadata: Annotated[
        dict[str, Any],
        Field(
            description="Caller-supplied opaque metadata. Kiln does not interpret this object."
        ),
    ]
    idempotency_key: Annotated[str | None, Field(min_length=1)] = None


class RunSpecification(RootModel[Schema_4]):
    root: Schema_4


class Mode(StrEnum):
    installation_default = "installation_default"
    unlimited = "unlimited"
    custom = "custom"


class ActiveCapabilityGrantReference(RootModel[str]):
    root: Annotated[str, Field(min_length=1)]


class Kind_1(StrEnum):
    tool_call = "tool_call"
    approval = "approval"
    external_job = "external_job"
    timer = "timer"
    callback = "callback"


class PendingOperationReference(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    kind: Annotated[Kind_1, Field(description="The kind of operation being awaited.")]
    id: Annotated[
        str,
        Field(description="Stable identifier for the pending operation.", min_length=1),
    ]
    correlation_id: Annotated[
        str | None,
        Field(
            description="Optional correlation identifier used to match callbacks or provider responses.",
            min_length=1,
        ),
    ] = None
    expires_at: Annotated[
        AwareDatetime | None,
        Field(
            description="Optional deadline after which the operation should be treated as expired."
        ),
    ] = None


class RecoveryMetadata(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    attempt: Annotated[int | None, Field(ge=0)] = None
    last_recovery_at: AwareDatetime | None = None
    last_error_id: Annotated[str | None, Field(min_length=1)] = None


class PinnedItemId(RootModel[str]):
    root: Annotated[str, Field(min_length=1)]


class AvailableItemId(RootModel[str]):
    root: Annotated[str, Field(min_length=1)]


class ActiveItemId(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    item_id: Annotated[str, Field(min_length=1)]
    order: Annotated[int, Field(ge=0)]


class ObservedItemId(RootModel[str]):
    root: Annotated[str, Field(min_length=1)]


class StaleItemId(RootModel[str]):
    root: Annotated[str, Field(min_length=1)]


class Schema_5(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    context_id: Annotated[str, Field(min_length=1)]
    pinned_item_ids: list[PinnedItemId] | None = None
    available_item_ids: list[AvailableItemId] | None = None
    active_item_ids: list[ActiveItemId] | None = None
    observed_item_ids: list[ObservedItemId] | None = None
    stale_item_ids: list[StaleItemId] | None = None
    current_token_estimate: Annotated[int, Field(ge=0)]
    model_context_limit: Annotated[int, Field(ge=0)]
    context_state_revision: Annotated[int, Field(ge=0)]


class SchemaModel_1(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    state_revision: Annotated[int, Field(ge=0)]
    latest_transaction_sequence: Annotated[int, Field(ge=0)]
    estimate_vs_actuals: dict[str, Any]
    mode: Mode
    model_input_tokens: BudgetDetails | None = None
    model_output_tokens: BudgetDetails | None = None
    model_calls: BudgetDetails | None = None
    tool_calls: BudgetDetails | None = None
    repository_requests: BudgetDetails | None = None
    elapsed_wall_time_seconds: BudgetDetails | None = None
    monetary_cost_usd: BudgetDetails | None = None
    command_time_seconds: BudgetDetails | None = None
    command_output_size_bytes: BudgetDetails | None = None
    artifact_size_bytes: BudgetDetails | None = None
    repeated_token_cost_usd: BudgetDetails | None = None


class SchemaModel1_1(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    lifecycle_state: lifecycle_state_1.Schema
    current_turn: Annotated[int, Field(ge=0)]
    current_task_state: task_state.Schema
    active_repository: identifier.Schema | None = None
    current_context_ledger_summary: Schema_5
    budget_summary: SchemaModel_1
    active_capability_grant_references: Annotated[
        list[ActiveCapabilityGrantReference], Field(min_length=1)
    ]
    pending_operation_reference: Annotated[
        PendingOperationReference | None,
        Field(
            description="Reference to the asynchronous operation the run is currently waiting on."
        ),
    ] = None
    last_committed_event_sequence: Annotated[int | None, Field(ge=0)] = None
    recovery_metadata: RecoveryMetadata | None = None
    terminal_result_reference: terminal_result_reference_1.Schema | None = None


class RunState(RootModel[SchemaModel1_1]):
    root: SchemaModel1_1
