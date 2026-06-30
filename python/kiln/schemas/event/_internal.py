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
    artifact_created,
    artifact_events,
    budget_events,
    context_events,
    context_item_admitted,
    context_item_available,
    context_item_evicted,
    context_plan_applied,
    context_plan_produced,
    context_plan_requested,
    context_rendered,
    envelope,
    identifier,
    model_events,
    model_invocation_started,
    model_request_rendered,
    model_response_interpreted,
    reference,
    repository_events,
    repository_preparation_completed,
    repository_preparation_started,
    repository_query_completed,
    repository_query_failed,
    repository_query_started,
    repository_session_closed,
    repository_session_opened,
    repository_version_pinned,
    repository_worker_started,
    run_completed,
    run_execution_started,
    run_failed,
    run_initialization_started,
    run_lifecycle_events,
    run_output_production_started,
    runtime_session_events,
    runtime_session_ready,
    runtime_session_started,
    turn_completed,
    turn_events,
    turn_failed,
    turn_started,
)
from . import changed_file_manifest_reference as changed_file_manifest_reference_1
from . import limits as limits_1
from . import model_invocation_completed as model_invocation_completed_1
from . import model_invocation_failed as model_invocation_failed_1
from . import output_mode as output_mode_1
from . import patch_reference as patch_reference_1
from . import report_reference as report_reference_1
from . import usage as usage_1


class EventModelEvents(RootModel[model_events.Schema]):
    root: model_events.Schema


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


class EventRepositoryEvents(RootModel[repository_events.Schema]):
    root: repository_events.Schema


class EventRunLifecycleEvents(RootModel[run_lifecycle_events.Schema]):
    root: run_lifecycle_events.Schema


class EventRuntimeSessionEvents(RootModel[runtime_session_events.Schema]):
    root: runtime_session_events.Schema


class EventTurnEvents(RootModel[turn_events.Schema]):
    root: turn_events.Schema


class EventArtifactEvents(RootModel[artifact_events.Schema]):
    root: artifact_events.Schema


class EventBudgetEvents(RootModel[budget_events.Schema]):
    root: budget_events.Schema


class EventContextEvents(RootModel[context_events.Schema]):
    root: context_events.Schema


class EventPayloadArtifactCreated(RootModel[artifact_created.Schema]):
    root: artifact_created.Schema


class EventPayloadContextItemAdmitted(RootModel[context_item_admitted.Schema]):
    root: context_item_admitted.Schema


class EventPayloadContextItemAvailable(RootModel[context_item_available.Schema]):
    root: context_item_available.Schema


class EventPayloadContextItemEvicted(RootModel[context_item_evicted.Schema]):
    root: context_item_evicted.Schema


class EventPayloadContextPlanApplied(RootModel[context_plan_applied.Schema]):
    root: context_plan_applied.Schema


class EventPayloadContextPlanProduced(RootModel[context_plan_produced.Schema]):
    root: context_plan_produced.Schema


class EventPayloadContextPlanRequested(RootModel[context_plan_requested.Schema]):
    root: context_plan_requested.Schema


class EventPayloadContextRendered(RootModel[context_rendered.Schema]):
    root: context_rendered.Schema


class EventPayloadModelInvocationCompleted(
    RootModel[model_invocation_completed_1.Schema]
):
    root: model_invocation_completed_1.Schema


class EventPayloadModelRequestRendered(RootModel[model_request_rendered.Schema]):
    root: model_request_rendered.Schema


class EventPayloadModelResponseInterpreted(
    RootModel[model_response_interpreted.Schema]
):
    root: model_response_interpreted.Schema


class EventPayloadRepositoryPreparationStarted(
    RootModel[repository_preparation_started.Schema]
):
    root: repository_preparation_started.Schema


class EventPayloadRepositoryQueryCompleted(
    RootModel[repository_query_completed.Schema]
):
    root: repository_query_completed.Schema


class EventPayloadRepositoryQueryStarted(RootModel[repository_query_started.Schema]):
    root: repository_query_started.Schema


class EventPayloadRepositoryVersionPinned(RootModel[repository_version_pinned.Schema]):
    root: repository_version_pinned.Schema


class EventPayloadRepositoryWorkerStarted(RootModel[repository_worker_started.Schema]):
    root: repository_worker_started.Schema


class Rule(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    rule_id: Annotated[str, Field(min_length=1)]
    effect: Effect
    priority: Annotated[int, Field(ge=0)]
    capability: Annotated[str, Field(min_length=1)]
    scope: Schema_13
    conditions: Conditions | None = None


class EventPayloadRunInitializationStarted(
    RootModel[run_initialization_started.Schema]
):
    root: run_initialization_started.Schema


class EventPayloadRunOutputProductionStarted(
    RootModel[run_output_production_started.Schema]
):
    root: run_output_production_started.Schema


class EventPayloadRuntimeSessionReady(RootModel[runtime_session_ready.Schema]):
    root: runtime_session_ready.Schema


class EventPayloadRuntimeSessionStarted(RootModel[runtime_session_started.Schema]):
    root: runtime_session_started.Schema


class EventPayloadTurnCompleted(RootModel[turn_completed.Schema]):
    root: turn_completed.Schema


class EventPayloadTurnStarted(RootModel[turn_started.Schema]):
    root: turn_started.Schema


class EventEnvelope(RootModel[envelope.Schema]):
    root: envelope.Schema


class EventPayloadModelInvocationStarted(RootModel[model_invocation_started.Schema]):
    root: model_invocation_started.Schema


class EventPayloadRunCompleted(RootModel[run_completed.Schema]):
    root: run_completed.Schema


class EventPayloadRunExecutionStarted(RootModel[run_execution_started.Schema]):
    root: run_execution_started.Schema


class EventPayloadRunFailed(RootModel[run_failed.Schema]):
    root: run_failed.Schema


class EventPayloadTurnFailed(RootModel[turn_failed.Schema]):
    root: turn_failed.Schema


class EventPayloadModelInvocationFailed(RootModel[model_invocation_failed_1.Schema]):
    root: model_invocation_failed_1.Schema


class EventPayloadRepositoryQueryFailed(RootModel[repository_query_failed.Schema]):
    root: repository_query_failed.Schema


class EventPayloadRepositorySessionClosed(RootModel[repository_session_closed.Schema]):
    root: repository_session_closed.Schema


class EventPayloadRepositorySessionOpened(RootModel[repository_session_opened.Schema]):
    root: repository_session_opened.Schema


class EventPayloadRepositoryPreparationCompleted(
    RootModel[repository_preparation_completed.Schema]
):
    root: repository_preparation_completed.Schema


class KilnEventGeneratedPythonModelsBundle(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    event_artifact_events: EventArtifactEvents | None = None
    event_budget_events: EventBudgetEvents | None = None
    event_context_events: EventContextEvents | None = None
    event_envelope: EventEnvelope | None = None
    event_model_events: EventModelEvents | None = None
    event_payload_artifact_created: EventPayloadArtifactCreated | None = None
    event_payload_budget_committed: EventPayloadBudgetCommitted | None = None
    event_payload_budget_denied: EventPayloadBudgetDenied | None = None
    event_payload_budget_exhausted: EventPayloadBudgetExhausted | None = None
    event_payload_budget_initialized: EventPayloadBudgetInitialized | None = None
    event_payload_budget_reconciled: EventPayloadBudgetReconciled | None = None
    event_payload_budget_reserved: EventPayloadBudgetReserved | None = None
    event_payload_context_item_admitted: EventPayloadContextItemAdmitted | None = None
    event_payload_context_item_available: EventPayloadContextItemAvailable | None = None
    event_payload_context_item_evicted: EventPayloadContextItemEvicted | None = None
    event_payload_context_plan_applied: EventPayloadContextPlanApplied | None = None
    event_payload_context_plan_produced: EventPayloadContextPlanProduced | None = None
    event_payload_context_plan_requested: EventPayloadContextPlanRequested | None = None
    event_payload_context_rendered: EventPayloadContextRendered | None = None
    event_payload_model_egress_evaluated: EventPayloadModelEgressEvaluated | None = None
    event_payload_model_invocation_completed: (
        EventPayloadModelInvocationCompleted | None
    ) = None
    event_payload_model_invocation_failed: EventPayloadModelInvocationFailed | None = (
        None
    )
    event_payload_model_invocation_started: (
        EventPayloadModelInvocationStarted | None
    ) = None
    event_payload_model_request_rendered: EventPayloadModelRequestRendered | None = None
    event_payload_model_response_interpreted: (
        EventPayloadModelResponseInterpreted | None
    ) = None
    event_payload_repository_preparation_completed: (
        EventPayloadRepositoryPreparationCompleted | None
    ) = None
    event_payload_repository_preparation_started: (
        EventPayloadRepositoryPreparationStarted | None
    ) = None
    event_payload_repository_query_completed: (
        EventPayloadRepositoryQueryCompleted | None
    ) = None
    event_payload_repository_query_failed: EventPayloadRepositoryQueryFailed | None = (
        None
    )
    event_payload_repository_query_started: (
        EventPayloadRepositoryQueryStarted | None
    ) = None
    event_payload_repository_session_closed: (
        EventPayloadRepositorySessionClosed | None
    ) = None
    event_payload_repository_session_opened: (
        EventPayloadRepositorySessionOpened | None
    ) = None
    event_payload_repository_version_pinned: (
        EventPayloadRepositoryVersionPinned | None
    ) = None
    event_payload_repository_worker_started: (
        EventPayloadRepositoryWorkerStarted | None
    ) = None
    event_payload_run_completed: EventPayloadRunCompleted | None = None
    event_payload_run_created: EventPayloadRunCreated | None = None
    event_payload_run_execution_started: EventPayloadRunExecutionStarted | None = None
    event_payload_run_failed: EventPayloadRunFailed | None = None
    event_payload_run_initialization_completed: (
        EventPayloadRunInitializationCompleted | None
    ) = None
    event_payload_run_initialization_started: (
        EventPayloadRunInitializationStarted | None
    ) = None
    event_payload_run_output_production_completed: (
        EventPayloadRunOutputProductionCompleted | None
    ) = None
    event_payload_run_output_production_started: (
        EventPayloadRunOutputProductionStarted | None
    ) = None
    event_payload_runtime_session_ready: EventPayloadRuntimeSessionReady | None = None
    event_payload_runtime_session_started: EventPayloadRuntimeSessionStarted | None = (
        None
    )
    event_payload_turn_completed: EventPayloadTurnCompleted | None = None
    event_payload_turn_failed: EventPayloadTurnFailed | None = None
    event_payload_turn_started: EventPayloadTurnStarted | None = None
    event_repository_events: EventRepositoryEvents | None = None
    event_run_lifecycle_events: EventRunLifecycleEvents | None = None
    event_runtime_session_events: EventRuntimeSessionEvents | None = None
    event_turn_events: EventTurnEvents | None = None


class Measurement(StrEnum):
    estimated = "estimated"
    actual = "actual"
    reconciled = "reconciled"


class CommitmentReason(StrEnum):
    model_invocation_completed = "model_invocation_completed"
    model_invocation_failed = "model_invocation_failed"
    tool_invocation_completed = "tool_invocation_completed"
    tool_invocation_failed = "tool_invocation_failed"
    repository_operation_completed = "repository_operation_completed"
    repository_operation_failed = "repository_operation_failed"
    artifact_written = "artifact_written"
    output_production_completed = "output_production_completed"
    validation_completed = "validation_completed"
    runtime_operation_completed = "runtime_operation_completed"
    other = "other"


class Schema(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    budget_id: Annotated[str, Field(min_length=1)]
    commitment_id: Annotated[
        str,
        Field(
            description="Identity for this committed budget transaction.", min_length=1
        ),
    ]
    reservation_id: Annotated[
        str | None,
        Field(
            description="Reservation this commitment consumes, when applicable.",
            min_length=1,
        ),
    ] = None
    usage: Annotated[
        usage_1.Schema, Field(description="Usage committed to the budget ledger.")
    ]
    measurement: Annotated[
        Measurement | None, Field(description="How the committed usage was measured.")
    ] = None
    commitment_reason: Annotated[
        CommitmentReason | None, Field(description="Reason budget was committed.")
    ] = None
    state_after: Annotated[
        Schema_15, Field(description="Budget state after committing usage.")
    ]
    committed_at: Annotated[
        AwareDatetime, Field(description="When budget usage was committed.")
    ]


class EventPayloadBudgetCommitted(RootModel[Schema]):
    root: Schema


class DeniedDimension(StrEnum):
    model_input_tokens = "model_input_tokens"
    model_output_tokens = "model_output_tokens"
    model_calls = "model_calls"
    tool_calls = "tool_calls"
    repository_requests = "repository_requests"
    elapsed_wall_time_seconds = "elapsed_wall_time_seconds"
    monetary_cost_usd = "monetary_cost_usd"
    command_time_seconds = "command_time_seconds"
    command_output_size_bytes = "command_output_size_bytes"
    artifact_size_bytes = "artifact_size_bytes"
    repeated_token_cost_usd = "repeated_token_cost_usd"


class DenialReason(StrEnum):
    limit_exceeded = "limit_exceeded"
    reservation_exceeds_remaining = "reservation_exceeds_remaining"
    budget_exhausted = "budget_exhausted"
    budget_not_initialized = "budget_not_initialized"
    invalid_request = "invalid_request"
    policy_denied = "policy_denied"
    unknown = "unknown"


class Schema_1(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    budget_id: Annotated[str, Field(min_length=1)]
    denial_id: Annotated[
        str,
        Field(description="Identity for this budget denial decision.", min_length=1),
    ]
    reservation_id: Annotated[
        str | None,
        Field(
            description="Reservation identity that was denied, when the denial occurred during reservation.",
            min_length=1,
        ),
    ] = None
    requested_amounts: Annotated[
        limits_1.Schema, Field(description="Budget amounts requested but denied.")
    ]
    denied_dimensions: Annotated[
        list[DeniedDimension] | None,
        Field(
            description="Budget dimensions that caused or contributed to denial.",
            min_length=1,
        ),
    ] = None
    denial_reason: Annotated[
        DenialReason, Field(description="Reason the budget request was denied.")
    ]
    state_at_denial: Annotated[
        Schema_15, Field(description="Budget state when the request was denied.")
    ]
    denied_at: Annotated[AwareDatetime, Field(description="When budget was denied.")]


class EventPayloadBudgetDenied(RootModel[Schema_1]):
    root: Schema_1


class ExhaustedDimension(StrEnum):
    model_input_tokens = "model_input_tokens"
    model_output_tokens = "model_output_tokens"
    model_calls = "model_calls"
    tool_calls = "tool_calls"
    repository_requests = "repository_requests"
    elapsed_wall_time_seconds = "elapsed_wall_time_seconds"
    monetary_cost_usd = "monetary_cost_usd"
    command_time_seconds = "command_time_seconds"
    command_output_size_bytes = "command_output_size_bytes"
    artifact_size_bytes = "artifact_size_bytes"
    repeated_token_cost_usd = "repeated_token_cost_usd"


class ExhaustionReason(StrEnum):
    committed_usage_reached_limit = "committed_usage_reached_limit"
    reservation_reached_limit = "reservation_reached_limit"
    reconciliation_reached_limit = "reconciliation_reached_limit"
    external_limit_reached = "external_limit_reached"
    unknown = "unknown"


class Schema_2(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    budget_id: Annotated[str, Field(min_length=1)]
    triggering_commitment_id: Annotated[
        str,
        Field(
            description="Commitment that caused exhaustion, when applicable.",
            min_length=1,
        ),
    ]
    triggering_reservation_id: Annotated[
        str | None,
        Field(
            description="Reservation that caused exhaustion, when applicable.",
            min_length=1,
        ),
    ] = None
    exhausted_dimensions: Annotated[
        list[ExhaustedDimension],
        Field(description="Budget dimensions that are exhausted.", min_length=1),
    ]
    exhaustion_reason: Annotated[
        ExhaustionReason | None, Field(description="Reason exhaustion was detected.")
    ] = None
    state_at_exhaustion: Annotated[
        Schema_15, Field(description="Budget state when exhaustion was detected.")
    ]
    exhausted_at: Annotated[
        AwareDatetime, Field(description="When budget exhaustion was detected.")
    ]


class SchemaModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    budget_id: Annotated[str, Field(min_length=1)]
    triggering_commitment_id: Annotated[
        str | None,
        Field(
            description="Commitment that caused exhaustion, when applicable.",
            min_length=1,
        ),
    ] = None
    triggering_reservation_id: Annotated[
        str,
        Field(
            description="Reservation that caused exhaustion, when applicable.",
            min_length=1,
        ),
    ]
    exhausted_dimensions: Annotated[
        list[ExhaustedDimension],
        Field(description="Budget dimensions that are exhausted.", min_length=1),
    ]
    exhaustion_reason: Annotated[
        ExhaustionReason | None, Field(description="Reason exhaustion was detected.")
    ] = None
    state_at_exhaustion: Annotated[
        Schema_15, Field(description="Budget state when exhaustion was detected.")
    ]
    exhausted_at: Annotated[
        AwareDatetime, Field(description="When budget exhaustion was detected.")
    ]


class SchemaModel1(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    budget_id: Annotated[str, Field(min_length=1)]
    triggering_commitment_id: Annotated[
        str | None,
        Field(
            description="Commitment that caused exhaustion, when applicable.",
            min_length=1,
        ),
    ] = None
    triggering_reservation_id: Annotated[
        str | None,
        Field(
            description="Reservation that caused exhaustion, when applicable.",
            min_length=1,
        ),
    ] = None
    exhausted_dimensions: Annotated[
        list[ExhaustedDimension],
        Field(description="Budget dimensions that are exhausted.", min_length=1),
    ]
    exhaustion_reason: Annotated[
        ExhaustionReason, Field(description="Reason exhaustion was detected.")
    ]
    state_at_exhaustion: Annotated[
        Schema_15, Field(description="Budget state when exhaustion was detected.")
    ]
    exhausted_at: Annotated[
        AwareDatetime, Field(description="When budget exhaustion was detected.")
    ]


class SchemaModel2(RootModel[Schema_2 | SchemaModel | SchemaModel1]):
    root: Annotated[
        Schema_2 | SchemaModel | SchemaModel1,
        Field(
            description="Payload for budget.exhausted events.",
            title="Kiln event payload budget exhausted",
        ),
    ]


class EventPayloadBudgetExhausted(RootModel[SchemaModel2]):
    root: SchemaModel2


class BudgetScope(StrEnum):
    run = "run"
    turn = "turn"
    operation = "operation"
    component = "component"


class Schema_3(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    budget_scope: Annotated[
        BudgetScope, Field(description="Scope controlled by this budget.")
    ]
    budget_id: Annotated[
        str,
        Field(
            description="Stable identity for this budget ledger or accounting scope.",
            min_length=1,
        ),
    ]
    run_id: Annotated[str | None, Field(min_length=1)] = None
    turn_id: Annotated[str | None, Field(min_length=1)] = None
    operation_id: Annotated[str | None, Field(min_length=1)] = None
    component: Annotated[str | None, Field(min_length=1)] = None
    limits: Annotated[
        limits_1.Schema, Field(description="Budget limits configured for this scope.")
    ]
    initial_state: Annotated[
        Schema_15, Field(description="Initial budget accounting state.")
    ]
    initialized_at: Annotated[
        AwareDatetime, Field(description="When this budget scope was initialized.")
    ]


class EventPayloadBudgetInitialized(RootModel[Schema_3]):
    root: Schema_3


class ReconciliationReason(StrEnum):
    estimated_to_actual = "estimated_to_actual"
    provider_usage_reported = "provider_usage_reported"
    reservation_expired = "reservation_expired"
    reservation_released = "reservation_released"
    manual_adjustment = "manual_adjustment"
    ledger_repair = "ledger_repair"
    run_finalization = "run_finalization"
    unknown = "unknown"


class Dimension(StrEnum):
    model_input_tokens = "model_input_tokens"
    model_output_tokens = "model_output_tokens"
    model_calls = "model_calls"
    tool_calls = "tool_calls"
    repository_requests = "repository_requests"
    elapsed_wall_time_seconds = "elapsed_wall_time_seconds"
    monetary_cost_usd = "monetary_cost_usd"
    command_time_seconds = "command_time_seconds"
    command_output_size_bytes = "command_output_size_bytes"
    artifact_size_bytes = "artifact_size_bytes"
    repeated_token_cost_usd = "repeated_token_cost_usd"


class Adjustment(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    dimension: Dimension
    adjustment_amount: Annotated[
        float,
        Field(
            description="Signed adjustment amount. Positive increases committed usage; negative decreases it."
        ),
    ]
    reason: Annotated[str | None, Field(min_length=1)] = None


class Schema_4(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    budget_id: Annotated[str, Field(min_length=1)]
    reconciliation_id: Annotated[
        str,
        Field(description="Identity for this reconciliation operation.", min_length=1),
    ]
    reconciliation_reason: Annotated[
        ReconciliationReason,
        Field(description="Reason the budget ledger was reconciled."),
    ]
    adjustments: Annotated[
        list[Adjustment] | None,
        Field(
            description="Usage adjustments applied during reconciliation.", min_length=1
        ),
    ] = None
    reconciled_usage: Annotated[
        usage_1.Schema | None,
        Field(description="Usage record produced by reconciliation, when applicable."),
    ] = None
    state_before: Annotated[
        Schema_15, Field(description="Budget state before reconciliation.")
    ]
    state_after: Annotated[
        Schema_15, Field(description="Budget state after reconciliation.")
    ]
    reconciled_at: Annotated[
        AwareDatetime, Field(description="When budget reconciliation completed.")
    ]


class EventPayloadBudgetReconciled(RootModel[Schema_4]):
    root: Schema_4


class ReservationScope(StrEnum):
    run = "run"
    turn = "turn"
    operation = "operation"
    component = "component"


class ReservationReason(StrEnum):
    model_invocation = "model_invocation"
    tool_invocation = "tool_invocation"
    repository_operation = "repository_operation"
    output_production = "output_production"
    validation = "validation"
    runtime_operation = "runtime_operation"
    other = "other"


class Schema_5(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    budget_id: Annotated[str, Field(min_length=1)]
    reservation_id: Annotated[
        str, Field(description="Identity for this budget reservation.", min_length=1)
    ]
    reservation_scope: Annotated[
        ReservationScope, Field(description="Scope for the reservation.")
    ]
    run_id: Annotated[str | None, Field(min_length=1)] = None
    turn_id: Annotated[str | None, Field(min_length=1)] = None
    operation_id: Annotated[str | None, Field(min_length=1)] = None
    component: Annotated[str | None, Field(min_length=1)] = None
    reserved_amounts: Annotated[
        limits_1.Schema, Field(description="Amounts reserved by dimension.")
    ]
    reservation_reason: Annotated[
        ReservationReason | None, Field(description="Reason budget was reserved.")
    ] = None
    expires_at: Annotated[
        AwareDatetime | None,
        Field(
            description="When this reservation expires if not committed or released."
        ),
    ] = None
    state_after: Annotated[
        Schema_15, Field(description="Budget state after applying the reservation.")
    ]
    reserved_at: Annotated[
        AwareDatetime, Field(description="When budget was reserved.")
    ]


class EventPayloadBudgetReserved(RootModel[Schema_5]):
    root: Schema_5


class Decision(StrEnum):
    granted = "granted"
    denied = "denied"


class Schema_6(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    decision: Annotated[
        Decision,
        Field(description="The decision that was made for this capability request"),
    ]
    grant: Annotated[
        Schema_7,
        Field(description="The grant that was issued for this capability request"),
    ]
    reason: Annotated[
        str,
        Field(
            description="The reason that this capability request was granted or denied",
            min_length=1,
        ),
    ]


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


class Schema_7(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    grant_id: Annotated[str, Field(min_length=1)]
    capability_type: CapabilityType
    run_id: Annotated[str, Field(min_length=1)]
    capability_scope: Schema_13
    allowed_operations: list[AllowedOperation_1]
    creation_source: CreationSource
    approval_metadata: ApprovalMetadata
    starts_at: AwareDatetime
    expires_at: AwareDatetime
    revoked: bool


class EgressDecision(StrEnum):
    allowed = "allowed"
    denied = "denied"
    redacted = "redacted"
    requires_approval = "requires_approval"


class RedactedItemId(RootModel[str]):
    root: Annotated[str, Field(min_length=1)]


class RedactionSummary(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    redaction_count: Annotated[int | None, Field(ge=0)] = None
    redacted_item_ids: list[RedactedItemId] | None = None
    reason: Annotated[str | None, Field(min_length=1)] = None


class Schema_8(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    model_invocation_id: Annotated[
        str,
        Field(
            description="Model invocation whose rendered request was evaluated for egress.",
            min_length=1,
        ),
    ]
    request_artifact_reference: Annotated[
        reference.Schema | None,
        Field(
            description="Optional artifact reference for the rendered request that was evaluated."
        ),
    ] = None
    egress_decision: Annotated[
        EgressDecision,
        Field(description="Decision produced by egress policy evaluation."),
    ]
    policy_decision_reference: Annotated[
        Schema_6 | None,
        Field(
            description="Optional capability decision produced by the egress policy check."
        ),
    ] = None
    redaction_summary: Annotated[
        RedactionSummary | None,
        Field(description="Summary of request changes made before model egress."),
    ] = None
    evaluated_at: Annotated[
        AwareDatetime, Field(description="When egress was evaluated.")
    ]


class EventPayloadModelEgressEvaluated(RootModel[Schema_8]):
    root: Schema_8


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


class Schema_9(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    requirement_id: Annotated[str, Field(min_length=1)]
    requirement_kind: RequirementKind
    severity: Severity
    trigger: Trigger
    scope: Schema_13 | None = None
    budget_limits: limits_1.Schema | None = None
    capability_requirements: Annotated[
        list[CapabilityRequirement] | None, Field(min_length=1)
    ] = None
    config: dict[str, Any]


class Schema_10(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    run_specification_id: Annotated[
        str,
        Field(
            description="The run specification that was used to create this run",
            min_length=1,
        ),
    ]
    task_id: Annotated[
        str,
        Field(description="The task that this run is associated with", min_length=1),
    ]
    task_hash: Annotated[
        str | None,
        Field(
            description="The hash of the task that this run is associated with",
            min_length=1,
        ),
    ] = None
    task_artifact_references: Annotated[
        list[reference.Schema] | None,
        Field(
            description="The artifact references that were used to create this run",
            min_length=1,
        ),
    ] = None
    repository: Annotated[
        identifier.Schema,
        Field(description="The repository that this run is associated with"),
    ]
    requested_model: Annotated[
        str,
        Field(description="The model that was requested for this run", min_length=1),
    ]
    requested_budgets: Annotated[
        limits_1.Schema,
        Field(description="The budgets that were requested for this run"),
    ]
    requested_security_profile: Annotated[
        SchemaModel8,
        Field(description="The security profile that was requested for this run"),
    ]
    validation_requirements: Annotated[
        list[Schema_9] | None,
        Field(
            description="The validation requirements that were requested for this run",
            min_length=1,
        ),
    ] = None


class SchemaModel_1(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    run_specification_id: Annotated[
        str,
        Field(
            description="The run specification that was used to create this run",
            min_length=1,
        ),
    ]
    task_id: Annotated[
        str | None,
        Field(description="The task that this run is associated with", min_length=1),
    ] = None
    task_hash: Annotated[
        str,
        Field(
            description="The hash of the task that this run is associated with",
            min_length=1,
        ),
    ]
    task_artifact_references: Annotated[
        list[reference.Schema] | None,
        Field(
            description="The artifact references that were used to create this run",
            min_length=1,
        ),
    ] = None
    repository: Annotated[
        identifier.Schema,
        Field(description="The repository that this run is associated with"),
    ]
    requested_model: Annotated[
        str,
        Field(description="The model that was requested for this run", min_length=1),
    ]
    requested_budgets: Annotated[
        limits_1.Schema,
        Field(description="The budgets that were requested for this run"),
    ]
    requested_security_profile: Annotated[
        SchemaModel8,
        Field(description="The security profile that was requested for this run"),
    ]
    validation_requirements: Annotated[
        list[Schema_9] | None,
        Field(
            description="The validation requirements that were requested for this run",
            min_length=1,
        ),
    ] = None


class SchemaModel1_1(RootModel[Schema_10 | SchemaModel_1]):
    root: Annotated[
        Schema_10 | SchemaModel_1, Field(title="Kiln event payload run created")
    ]


class EventPayloadRunCreated(RootModel[SchemaModel1_1]):
    root: SchemaModel1_1


class SelectedAdapterId(RootModel[str]):
    root: Annotated[str, Field(min_length=1)]


class Schema_11(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    effective_budgets: Annotated[
        Schema_15, Field(description="The budgets that were effective for this run")
    ]
    effective_capability_profile: Annotated[
        SchemaModel8,
        Field(description="The capability profile that was effective for this run"),
    ]
    selected_adapter_ids: Annotated[
        list[SelectedAdapterId] | None,
        Field(description="The adapters that were selected for this run", min_length=1),
    ] = None
    deadline: Annotated[
        AwareDatetime | None, Field(description="The deadline for this run, if any")
    ] = None
    initialization_duration: Annotated[
        int,
        Field(description="The duration of the initialization phase of this run", ge=0),
    ]


class EventPayloadRunInitializationCompleted(RootModel[Schema_11]):
    root: Schema_11


class Schema_12(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    report_reference: Annotated[
        report_reference_1.Schema | None,
        Field(description="The report reference that was produced by this run"),
    ] = None
    final_answer_artifact_reference: Annotated[
        answer_reference.Schema | None,
        Field(description="The artifact reference that was produced by this run"),
    ] = None
    patch_reference: Annotated[
        patch_reference_1.Schema | None,
        Field(description="The patch reference that was produced by this run"),
    ] = None
    changed_file_manifest_reference: Annotated[
        changed_file_manifest_reference_1.Schema | None,
        Field(
            description="The changed file manifest reference that was produced by this run"
        ),
    ] = None
    output_mode: Annotated[
        output_mode_1.Schema,
        Field(description="The output mode that was used by this run"),
    ]
    usage: Annotated[
        usage_1.Schema, Field(description="The usage that was produced by this run")
    ]
    validation_requirements: Annotated[
        list[Schema_9] | None,
        Field(
            description="The validation requirements that were produced by this run",
            min_length=1,
        ),
    ] = None


class EventPayloadRunOutputProductionCompleted(RootModel[Schema_12]):
    root: Schema_12


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


class Schema_13(BaseModel):
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


class Schema_14(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    filesystem_read_scopes: Annotated[list[Schema_13] | None, Field(min_length=1)] = (
        None
    )
    filesystem_write_scopes: Annotated[list[Schema_13] | None, Field(min_length=1)] = (
        None
    )
    process_execution_rules: Annotated[list[Rule] | None, Field(min_length=1)] = None
    network_rules: Annotated[list[Rule] | None, Field(min_length=1)] = None
    model_egress_rules: Annotated[list[Rule] | None, Field(min_length=1)] = None
    external_integration_rules: Annotated[list[Rule] | None, Field(min_length=1)] = None
    artifact_access_rules: Annotated[list[Rule] | None, Field(min_length=1)] = None
    validation_rules: Annotated[list[Rule] | None, Field(min_length=1)] = None
    default_deny_settings: DefaultDenySettings


class SchemaModel_2(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    filesystem_read_scopes: Annotated[list[Schema_13], Field(min_length=1)]
    filesystem_write_scopes: Annotated[list[Schema_13] | None, Field(min_length=1)] = (
        None
    )
    process_execution_rules: Annotated[list[Rule] | None, Field(min_length=1)] = None
    network_rules: Annotated[list[Rule] | None, Field(min_length=1)] = None
    model_egress_rules: Annotated[list[Rule] | None, Field(min_length=1)] = None
    external_integration_rules: Annotated[list[Rule] | None, Field(min_length=1)] = None
    artifact_access_rules: Annotated[list[Rule] | None, Field(min_length=1)] = None
    validation_rules: Annotated[list[Rule] | None, Field(min_length=1)] = None
    default_deny_settings: DefaultDenySettings | None = None


class SchemaModel1_2(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    filesystem_read_scopes: Annotated[list[Schema_13] | None, Field(min_length=1)] = (
        None
    )
    filesystem_write_scopes: Annotated[list[Schema_13], Field(min_length=1)]
    process_execution_rules: Annotated[list[Rule] | None, Field(min_length=1)] = None
    network_rules: Annotated[list[Rule] | None, Field(min_length=1)] = None
    model_egress_rules: Annotated[list[Rule] | None, Field(min_length=1)] = None
    external_integration_rules: Annotated[list[Rule] | None, Field(min_length=1)] = None
    artifact_access_rules: Annotated[list[Rule] | None, Field(min_length=1)] = None
    validation_rules: Annotated[list[Rule] | None, Field(min_length=1)] = None
    default_deny_settings: DefaultDenySettings | None = None


class SchemaModel2_1(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    filesystem_read_scopes: Annotated[list[Schema_13] | None, Field(min_length=1)] = (
        None
    )
    filesystem_write_scopes: Annotated[list[Schema_13] | None, Field(min_length=1)] = (
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
    filesystem_read_scopes: Annotated[list[Schema_13] | None, Field(min_length=1)] = (
        None
    )
    filesystem_write_scopes: Annotated[list[Schema_13] | None, Field(min_length=1)] = (
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
    filesystem_read_scopes: Annotated[list[Schema_13] | None, Field(min_length=1)] = (
        None
    )
    filesystem_write_scopes: Annotated[list[Schema_13] | None, Field(min_length=1)] = (
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
    filesystem_read_scopes: Annotated[list[Schema_13] | None, Field(min_length=1)] = (
        None
    )
    filesystem_write_scopes: Annotated[list[Schema_13] | None, Field(min_length=1)] = (
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
    filesystem_read_scopes: Annotated[list[Schema_13] | None, Field(min_length=1)] = (
        None
    )
    filesystem_write_scopes: Annotated[list[Schema_13] | None, Field(min_length=1)] = (
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
    filesystem_read_scopes: Annotated[list[Schema_13] | None, Field(min_length=1)] = (
        None
    )
    filesystem_write_scopes: Annotated[list[Schema_13] | None, Field(min_length=1)] = (
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
        Schema_14
        | SchemaModel_2
        | SchemaModel1_2
        | SchemaModel2_1
        | SchemaModel3
        | SchemaModel4
        | SchemaModel5
        | SchemaModel6
        | SchemaModel7
    ]
):
    root: Annotated[
        Schema_14
        | SchemaModel_2
        | SchemaModel1_2
        | SchemaModel2_1
        | SchemaModel3
        | SchemaModel4
        | SchemaModel5
        | SchemaModel6
        | SchemaModel7,
        Field(title="Kiln capability security profile"),
    ]


class Mode(StrEnum):
    installation_default = "installation_default"
    unlimited = "unlimited"
    custom = "custom"


class Schema_15(BaseModel):
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
