"""
Generated Pydantic v2 models for Kiln JSON Schemas.

Do not edit this package by hand. Regenerate with:

    uv run generatemodels
"""

from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field


class Client(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    name: Annotated[str, Field(description="The name of the client.", min_length=1)]
    version: Annotated[
        str, Field(description="The version of the client.", min_length=1)
    ]


class Schema(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    protocol_version: Annotated[
        str,
        Field(
            description="The version of the Kiln runtime protocol that the client supports.",
            min_length=1,
        ),
    ]
    schema_set_version: Annotated[
        str,
        Field(
            description="The version of the Kiln runtime schema set that the client supports.",
            min_length=1,
        ),
    ]
    compatibility_major: Annotated[
        int,
        Field(
            description="The major version of the Kiln runtime protocol that the client supports.",
            ge=0,
        ),
    ]
    client: Annotated[
        Client,
        Field(
            description="Information about the client that is initializing the runtime."
        ),
    ]
