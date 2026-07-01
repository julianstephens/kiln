import json
from pathlib import Path

import pytest

from kiln.protocol.errors import KilnPayloadValidationError, UnsupportedMethodError
from kiln.protocol.jsonrpc import (
    JsonRpcErrorObject,
    JsonRpcErrorResponse,
    JsonRpcRequest,
    JsonRpcSuccessResponse,
)
from kiln.protocol.method import (
    validate_error_data,
    validate_request_params,
    validate_success_result,
)
from kiln.schemas.repository import (
    RepositoryError,
    RepositorySearchRequestPayload,
    RepositorySearchResult,
)

FIXTURES_ROOT = (
    Path(__file__).resolve().parents[4] / "schemas" / "fixtures" / "valid" / "v1"
)


def _load_fixture(name: str) -> dict:
    return json.loads((FIXTURES_ROOT / name).read_text())


def test_unknown_method_rejected_as_unsupported() -> None:
    req = JsonRpcRequest(
        jsonrpc="2.0",
        id="1",
        method="unknown.method",
        params={},
    )

    with pytest.raises(UnsupportedMethodError, match="unsupported JSON-RPC method"):
        validate_request_params(req)


def test_repository_search_params_validated_against_schema() -> None:
    req = JsonRpcRequest(
        jsonrpc="2.0",
        id="1",
        method="repository.search",
        params=_load_fixture("repository-search-request-payload-basic.json"),
    )

    result = validate_request_params(req)

    assert isinstance(result, RepositorySearchRequestPayload)


def test_repository_search_result_validated_when_method_supplied() -> None:
    resp = JsonRpcSuccessResponse(
        jsonrpc="2.0",
        id="1",
        result=_load_fixture("repository-search-result-basic.json"),
    )

    result = validate_success_result(method="repository.search", response=resp)

    assert isinstance(result, RepositorySearchResult)


def test_repository_search_error_data_validated_when_method_supplied() -> None:
    resp = JsonRpcErrorResponse(
        jsonrpc="2.0",
        id="1",
        error=JsonRpcErrorObject(
            code=-32001,
            message="repository error",
            data=_load_fixture("repository-error-basic.json"),
        ),
    )

    result = validate_error_data(method="repository.search", response=resp)

    assert isinstance(result, RepositoryError)


def test_invalid_error_data_wrapped_consistently() -> None:
    resp = JsonRpcErrorResponse(
        jsonrpc="2.0",
        id="1",
        error=JsonRpcErrorObject(
            code=-32001,
            message="repository error",
            data={"foo": "bar"},
        ),
    )

    with pytest.raises(
        KilnPayloadValidationError,
        match=r"invalid Kiln payload: method=repository.search, part=error\.data",
    ):
        validate_error_data(method="repository.search", response=resp)
