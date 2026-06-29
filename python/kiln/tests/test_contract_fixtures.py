from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from kiln.schemas import EventEnvelope, RepositorySearchRequestPayload

REPO_ROOT = Path(__file__).resolve().parents[3]
FIXTURE_ROOT = REPO_ROOT / "contract-fixtures" / "v1"


def load_fixture(name: str) -> dict[str, Any]:
    with (FIXTURE_ROOT / name).open(encoding="utf-8") as file:
        data = json.load(file)

    assert isinstance(data, dict)
    return data


def assert_round_trips(model_type: type[Any], fixture_name: str) -> None:
    data = load_fixture(fixture_name)
    model = model_type.model_validate(data)

    serialized = json.loads(
        model.model_dump_json(
            by_alias=True,
            exclude_none=True,
        )
    )

    assert serialized == data


@pytest.mark.parametrize(
    ("model_type", "fixture_name"),
    [
        (EventEnvelope, "event-envelope.valid.json"),
        (
            RepositorySearchRequestPayload,
            "repository-search-request-payload.valid.json",
        ),
    ],
)
def test_contract_fixture_validates_and_serializes(model_type: type[Any], fixture_name: str) -> None:
    assert_round_trips(model_type, fixture_name)


def test_invalid_contract_fixture_fails_python_validation() -> None:
    data = load_fixture("repository-search-request-payload.invalid.missing-query.json")

    with pytest.raises(ValidationError):
        RepositorySearchRequestPayload.model_validate(data)
