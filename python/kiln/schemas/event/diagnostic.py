"""
Generated Pydantic v2 models for Kiln JSON Schemas.

Do not edit this package by hand. Regenerate with:

    uv run generatemodels
"""

from __future__ import annotations

from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

from . import reference, source_range


class DiagnosticCode(StrEnum):
    parse_failure = "parse_failure"
    unsupported_language = "unsupported_language"
    unresolved_reference = "unresolved_reference"
    truncated_source = "truncated_source"
    graph_confidence_warning = "graph_confidence_warning"
    summary_generation_warning = "summary_generation_warning"
    ignored_file = "ignored_file"
    oversized_file_skipped = "oversized_file_skipped"


class Severity(StrEnum):
    error = "error"
    warning = "warning"
    info = "info"


class Schema(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    diagnostic_code: DiagnosticCode
    severity: Severity
    path: Annotated[str | None, Field(min_length=1)] = None
    range: source_range.Schema | None = None
    content_id: Annotated[str, Field(min_length=1)]
    message: Annotated[str, Field(min_length=1)]
    related_artifacts: list[reference.Schema] | None = None
