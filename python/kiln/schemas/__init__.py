"""
Generated Pydantic v2 models for Kiln JSON Schemas.

Do not edit this package by hand. Regenerate with:

    uv run generatemodels
"""

from __future__ import annotations

from importlib import import_module
from types import ModuleType

__all__ = [
    "common",
    "artifact",
    "budget",
    "capability",
    "context",
    "event",
    "model",
    "repository",
    "run",
    "runtime",
    "validation",
    "workspace",
]

def __getattr__(name: str) -> ModuleType:
    if name not in __all__:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module = import_module(f"{__name__}.{name}")
    globals()[name] = module
    return module
