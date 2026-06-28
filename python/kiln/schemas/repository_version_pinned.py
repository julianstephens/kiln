"""
Generated Pydantic v2 models for Kiln JSON Schemas.

Do not edit this package by hand. Regenerate with:

    uv run generatemodels
"""

from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field


class Schema(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    repository_version_id: Annotated[
        str, Field(description="The repository version that was pinned.", min_length=1)
    ]
    source_revision: Annotated[
        str, Field(description="The source revision that was pinned.", min_length=1)
    ]
    content_digest: Annotated[
        str,
        Field(
            description="The content digest of the repository version that was pinned.",
            min_length=1,
        ),
    ]
