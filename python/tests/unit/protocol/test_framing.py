import json
from pathlib import Path

import pytest
from pytest_mock import MockerFixture

from kiln.protocol import framing
from kiln.protocol.errors import (
    EmbeddedNewlineInMessageError,
    FramingError,
    JsonRpcFrameExceedsSizeLimitError,
)
from kiln.protocol.framing import validate_frame
from kiln.schemas import (
    RepositoryError,
    RepositorySearchRequestPayload,
    RepositorySearchResult,
)

FIXTURES_ROOT = (
    Path(__file__).resolve().parents[4] / "schemas" / "fixtures" / "valid" / "v1"
)


def _load_fixture(name: str) -> dict:
    return json.loads((FIXTURES_ROOT / name).read_text())


def test_validate_frame_accepts_valid_request_and_validates_params_with_mocker(
    mocker: MockerFixture,
) -> None:
    payload = _load_fixture("repository-search-request-payload-basic.json")
    expected_payload = RepositorySearchRequestPayload.model_validate(
        payload
    ).model_dump(round_trip=True, mode="json")
    spy = mocker.spy(framing, "validate_kiln_schema")
    frame = validate_frame(
        json.dumps(
            {
                "jsonrpc": "2.0",
                "id": "req-1",
                "method": "repository.search",
                "params": payload,
            }
        ).encode()
    )

    assert frame["jsonrpc"] == "2.0"
    assert frame["method"] == "repository.search"
    assert frame["params"] == expected_payload
    assert frame.get("result") is None
    assert frame.get("error") is None
    spy.assert_called_once()
    assert spy.call_args.kwargs["data_type"] == "request"


def test_validate_frame_accepts_valid_response() -> None:
    payload = _load_fixture("repository-search-result-basic.json")
    expected_payload = RepositorySearchResult.model_validate(payload).model_dump(
        round_trip=True, mode="json"
    )

    frame = validate_frame(
        json.dumps(
            {
                "jsonrpc": "2.0",
                "id": "res-1",
                "method": "repository.search",
                "result": payload,
            },
            default=str,
        ).encode()
    )

    assert frame["jsonrpc"] == "2.0"
    assert frame["method"] == "repository.search"
    assert frame.get("params") is None
    assert frame["result"] == expected_payload
    assert "error" not in frame


def test_validate_frame_accepts_valid_error() -> None:
    payload = _load_fixture("repository-error-basic.json")
    expected_payload = RepositoryError.model_validate(payload).model_dump(
        round_trip=True, mode="json"
    )

    frame = validate_frame(
        json.dumps(
            {
                "jsonrpc": "2.0",
                "id": "err-1",
                "method": "repository.search",
                "error": {
                    "code": -32001,
                    "message": "repository error",
                    "data": payload,
                },
            }
        ).encode()
    )

    assert frame["jsonrpc"] == "2.0"
    assert frame["method"] == "repository.search"
    assert frame.get("params") is None
    assert frame.get("result") is None
    assert frame["error"] == {
        "code": -32001,
        "message": "repository error",
        "data": expected_payload,
    }


def test_validate_frame_accepts_success_response_without_method() -> None:
    payload = _load_fixture("repository-search-result-basic.json")

    frame = validate_frame(
        json.dumps(
            {
                "jsonrpc": "2.0",
                "id": "res-1",
                "result": payload,
            },
            default=str,
        ).encode()
    )

    assert frame["jsonrpc"] == "2.0"
    assert frame["id"] == "res-1"
    assert "method" not in frame
    assert frame["result"] == payload


def test_validate_frame_accepts_error_response_without_method() -> None:
    payload = _load_fixture("repository-error-basic.json")

    frame = validate_frame(
        json.dumps(
            {
                "jsonrpc": "2.0",
                "id": "err-1",
                "error": {
                    "code": -32001,
                    "message": "repository error",
                    "data": payload,
                },
            }
        ).encode()
    )

    assert frame["jsonrpc"] == "2.0"
    assert frame["id"] == "err-1"
    assert "method" not in frame
    assert frame["error"] == {
        "code": -32001,
        "message": "repository error",
        "data": payload,
    }


def test_validate_frame_rejects_oversized_message() -> None:
    with pytest.raises(JsonRpcFrameExceedsSizeLimitError):
        validate_frame(b"{}", max_message_bytes=1)


def test_validate_frame_rejects_embedded_newline() -> None:
    with pytest.raises(EmbeddedNewlineInMessageError):
        validate_frame(b'{"jsonrpc":"2.0"}\n')


def test_validate_frame_rejects_malformed_json() -> None:
    with pytest.raises(FramingError, match="invalid JSON-RPC frame"):
        validate_frame(b'{"jsonrpc":"2.0","id":"1"')


def test_validate_frame_rejects_non_object_payload() -> None:
    with pytest.raises(FramingError, match="must be a JSON object"):
        validate_frame(json.dumps(["not", "an", "object"]).encode())


def test_validate_frame_rejects_unexpected_field() -> None:
    payload = _load_fixture("repository-search-request-payload-basic.json")
    with pytest.raises(FramingError, match="unexpected field 'extra'"):
        validate_frame(
            json.dumps(
                {
                    "jsonrpc": "2.0",
                    "id": "req-2",
                    "method": "repository.search",
                    "params": payload,
                    "extra": True,
                }
            ).encode()
        )


def test_validate_frame_requires_jsonrpc() -> None:
    with pytest.raises(FramingError, match="missing required field 'jsonrpc'"):
        validate_frame(json.dumps({"id": "1", "method": "repository.search"}).encode())


def test_validate_frame_requires_supported_jsonrpc_version() -> None:
    with pytest.raises(FramingError, match="unsupported jsonrpc version"):
        validate_frame(
            json.dumps(
                {
                    "jsonrpc": "1.0",
                    "id": "1",
                    "method": "repository.search",
                    "params": _load_fixture(
                        "repository-search-request-payload-basic.json"
                    ),
                }
            ).encode()
        )


def test_validate_frame_requires_id() -> None:
    with pytest.raises(FramingError, match="missing required field 'id'"):
        validate_frame(
            json.dumps(
                {
                    "jsonrpc": "2.0",
                    "method": "repository.search",
                    "params": _load_fixture(
                        "repository-search-request-payload-basic.json"
                    ),
                }
            ).encode()
        )


def test_validate_frame_requires_method() -> None:
    with pytest.raises(FramingError, match="missing required field 'method'"):
        validate_frame(
            json.dumps(
                {
                    "jsonrpc": "2.0",
                    "id": "1",
                    "params": _load_fixture(
                        "repository-search-request-payload-basic.json"
                    ),
                }
            ).encode()
        )


def test_validate_frame_rejects_unsupported_method() -> None:
    with pytest.raises(FramingError, match=r"unsupported method 'unknown\.method'"):
        validate_frame(
            json.dumps(
                {
                    "jsonrpc": "2.0",
                    "id": "1",
                    "method": "unknown.method",
                    "params": {},
                }
            ).encode()
        )


def test_unknown_method_is_jsonrpc_valid_but_invalid_at_method_layer() -> None:
    frame = {
        "jsonrpc": "2.0",
        "id": "1",
        "method": "unknown.method",
        "params": {},
    }

    with pytest.raises(FramingError, match=r"unsupported method 'unknown\.method'"):
        validate_frame(json.dumps(frame).encode())


def test_validate_frame_rejects_when_no_payload_present() -> None:
    with pytest.raises(FramingError, match="no valid payload found"):
        validate_frame(
            json.dumps(
                {
                    "jsonrpc": "2.0",
                    "id": "1",
                    "method": "repository.search",
                }
            ).encode()
        )


def test_validate_frame_rejects_result_and_error_together() -> None:
    with pytest.raises(FramingError, match="cannot have both 'result' and 'error'"):
        validate_frame(
            json.dumps(
                {
                    "jsonrpc": "2.0",
                    "id": "1",
                    "method": "repository.search",
                    "result": _load_fixture("repository-search-result-basic.json"),
                    "error": {
                        "code": -32001,
                        "message": "repository error",
                        "data": _load_fixture("repository-error-basic.json"),
                    },
                }
            ).encode()
        )


def test_error_data_contains_kiln_specific_details() -> None:
    payload = _load_fixture("repository-error-basic.json")
    expected_payload = RepositoryError.model_validate(payload).model_dump(
        round_trip=True, mode="json"
    )

    frame = validate_frame(
        json.dumps(
            {
                "jsonrpc": "2.0",
                "id": "err-1",
                "method": "repository.search",
                "error": {
                    "code": -32001,
                    "message": "repository error",
                    "data": payload,
                },
            }
        ).encode()
    )

    assert frame["error"]["data"] == expected_payload


def test_validate_frame_rejects_invalid_request_payload_shape() -> None:
    with pytest.raises(FramingError, match="payload validation failed"):
        validate_frame(
            json.dumps(
                {
                    "jsonrpc": "2.0",
                    "id": "1",
                    "method": "repository.search",
                    "params": {"session_id": "abc"},
                }
            ).encode()
        )


def test_validate_frame_rejects_non_object_payload_field() -> None:
    with pytest.raises(FramingError, match="request must be a JSON object"):
        validate_frame(
            json.dumps(
                {
                    "jsonrpc": "2.0",
                    "id": "1",
                    "method": "repository.search",
                    "params": "not-an-object",
                }
            ).encode()
        )
