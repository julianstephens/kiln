"""
Generated Pydantic v2 models for Kiln JSON Schemas.

Do not edit this package by hand. Regenerate with:

    uv run generatemodels
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, RootModel

from . import configuration, error, generate_payload, generate_result, usage


class ModelUsage(RootModel[usage.Schema]):
    root: usage.Schema


class ModelConfiguration(RootModel[configuration.SchemaModel1]):
    root: configuration.SchemaModel1


class ModelError(RootModel[error.Schema]):
    root: error.Schema


class ModelGeneratePayload(RootModel[generate_payload.SchemaModel1]):
    root: generate_payload.SchemaModel1


class ModelGenerateResult(RootModel[generate_result.SchemaModel3]):
    root: generate_result.SchemaModel3


class KilnModelGeneratedPythonModelsBundle(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    model_configuration: ModelConfiguration | None = None
    model_error: ModelError | None = None
    model_generate_payload: ModelGeneratePayload | None = None
    model_generate_result: ModelGenerateResult | None = None
    model_usage: ModelUsage | None = None
