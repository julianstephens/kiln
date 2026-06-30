"""
Generated Pydantic v2 models for Kiln JSON Schemas.

Do not edit this package by hand. Regenerate with:

    uv run generatemodels
"""

from __future__ import annotations

from enum import StrEnum


class Schema(StrEnum):
    repository_preparation_started = "repository.preparation_started"
    repository_version_pinned = "repository.version_pinned"
    repository_preparation_completed = "repository.preparation_completed"
    repository_session_opened = "repository.session_opened"
    repository_session_closed = "repository.session_closed"
    repository_query_started = "repository.query_started"
    repository_query_completed = "repository.query_completed"
    repository_query_failed = "repository.query_failed"
    repository_worker_started = "repository.worker_started"
