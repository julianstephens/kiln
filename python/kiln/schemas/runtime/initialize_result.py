"""
Generated Pydantic v2 models for Kiln JSON Schemas.

Do not edit this package by hand. Regenerate with:

    uv run generatemodels
"""

from __future__ import annotations

from typing import Annotated

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, RootModel


class Runtime(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    id: Annotated[
        str, Field(description="The unique identifier of the runtime.", min_length=1)
    ]
    name: Annotated[str, Field(description="The name of the runtime.", min_length=1)]
    version: Annotated[
        str, Field(description="The version of the runtime.", min_length=1)
    ]


class SupportedMethodNamespace(RootModel[str]):
    root: Annotated[str, Field(min_length=1)]


class SupportedMethod(RootModel[str]):
    root: Annotated[str, Field(min_length=1)]


class Build(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    commit: Annotated[
        str, Field(description="The commit hash of the build.", min_length=1)
    ]
    date: Annotated[
        AwareDatetime, Field(description="The date of the build in ISO 8601 format.")
    ]


class Schema(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    runtime: Annotated[
        Runtime,
        Field(description="Information about the runtime that was initialized."),
    ]
    protocol_version: Annotated[
        str,
        Field(
            description="The version of the Kiln runtime protocol that the runtime supports.",
            min_length=1,
        ),
    ]
    schema_set_version: Annotated[
        str,
        Field(
            description="The version of the Kiln runtime schema set that the runtime supports.",
            min_length=1,
        ),
    ]
    compatibility_major: Annotated[
        int,
        Field(
            description="The major version of the Kiln runtime protocol that the runtime supports.",
            ge=0,
        ),
    ]
    supported_method_namespaces: Annotated[
        list[SupportedMethodNamespace],
        Field(description="The list of method namespaces that the runtime supports."),
    ]
    supported_methods: Annotated[
        list[SupportedMethod],
        Field(description="The list of methods that the runtime supports."),
    ]
    build: Annotated[
        Build, Field(description="Information about the build of the runtime.")
    ]
