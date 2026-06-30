"""
Generated Pydantic v2 models for Kiln JSON Schemas.

Do not edit this package by hand. Regenerate with:

    uv run generatemodels
"""

from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

from . import alternative_representation, identifier
from . import content as content_1
from . import cost as cost_1
from . import provenance as provenance_1
from . import relevance as relevance_1
from . import source as source_1
from . import validity as validity_1


class Schema(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    content_id: Annotated[str, Field(min_length=1)]
    repository: identifier.Schema
    semantic_kind: Annotated[str, Field(min_length=1)]
    representation_kind: Annotated[str, Field(min_length=1)]
    source: source_1.Schema
    content: content_1.SchemaModel2
    cost: cost_1.Schema
    relevance: relevance_1.Schema
    provenance: provenance_1.SchemaModel1
    validity: validity_1.Schema
    alternative_representations: list[alternative_representation.Schema]
