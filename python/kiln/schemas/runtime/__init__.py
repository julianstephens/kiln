"""
Generated Pydantic v2 models for Kiln JSON Schemas.

Do not edit this package by hand. Regenerate with:

    uv run generatemodels
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, RootModel

from . import error, initialize_request_payload, initialize_result


class RuntimeError(RootModel[error.Schema]):
    root: error.Schema


class RuntimeInitializeRequestPayload(RootModel[initialize_request_payload.Schema]):
    root: initialize_request_payload.Schema


class RuntimeInitializeResult(RootModel[initialize_result.Schema]):
    root: initialize_result.Schema


class KilnRuntimeGeneratedPythonModelsBundle(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    runtime_error: RuntimeError | None = None
    runtime_initialize_request_payload: RuntimeInitializeRequestPayload | None = None
    runtime_initialize_result: RuntimeInitializeResult | None = None
