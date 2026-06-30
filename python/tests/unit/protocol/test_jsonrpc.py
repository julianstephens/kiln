import pytest

from kiln.protocol.errors import InvalidJsonRpcFrameError
from kiln.protocol.jsonrpc import (
    JsonRpcErrorResponse,
    JsonRpcRequest,
    JsonRpcSuccessResponse,
    parse_jsonrpc_message,
)


def test_parse_jsonrpc_valid_request_accepted() -> None:
    msg = parse_jsonrpc_message(
        {
            "jsonrpc": "2.0",
            "id": "1",
            "method": "repository.search",
            "params": {"query": "foo"},
        }
    )

    assert isinstance(msg, JsonRpcRequest)
    assert msg.method == "repository.search"


def test_parse_jsonrpc_unknown_method_request_accepted() -> None:
    msg = parse_jsonrpc_message(
        {
            "jsonrpc": "2.0",
            "id": "1",
            "method": "unknown.method",
            "params": {},
        }
    )

    assert isinstance(msg, JsonRpcRequest)
    assert msg.method == "unknown.method"


def test_parse_jsonrpc_success_response_without_method_accepted() -> None:
    msg = parse_jsonrpc_message(
        {
            "jsonrpc": "2.0",
            "id": "1",
            "result": {"ok": True},
        }
    )

    assert isinstance(msg, JsonRpcSuccessResponse)
    assert msg.result == {"ok": True}


def test_parse_jsonrpc_error_response_with_null_id_accepted() -> None:
    msg = parse_jsonrpc_message(
        {
            "jsonrpc": "2.0",
            "id": None,
            "error": {"code": -32000, "message": "boom", "data": {"x": 1}},
        }
    )

    assert isinstance(msg, JsonRpcErrorResponse)
    assert msg.id is None


def test_parse_jsonrpc_result_and_error_together_rejected() -> None:
    with pytest.raises(InvalidJsonRpcFrameError, match="mutually exclusive"):
        parse_jsonrpc_message(
            {
                "jsonrpc": "2.0",
                "id": "1",
                "result": {},
                "error": {"code": -32000, "message": "boom"},
            }
        )


def test_parse_jsonrpc_params_without_method_rejected() -> None:
    with pytest.raises(InvalidJsonRpcFrameError, match="params' field without 'method"):
        parse_jsonrpc_message(
            {
                "jsonrpc": "2.0",
                "id": "1",
                "params": {"query": "foo"},
            }
        )
