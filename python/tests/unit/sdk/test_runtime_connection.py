from __future__ import annotations

from types import SimpleNamespace
from typing import Any, get_args

import pytest

from kiln.protocol.jsonrpc import (
    DEFAULT_JSONRPC_VERSION,
    JsonRpcErrorObject,
    JsonRpcErrorResponse,
    JsonRpcRequest,
    JsonRpcSuccessResponse,
)
from kiln.schemas import COMPATIBILITY_MAJOR, SCHEMA_SET_VERSION
from kiln.sdk import PACKAGE_NAME, __version__
from kiln.sdk.errors import RuntimeProcessError
from kiln.sdk.runtime_connection import RuntimeStdioConnection


class _FakePeer:
    def __init__(self, response: Any) -> None:
        self._response = response
        self.last_request: JsonRpcRequest | None = None

    async def request(self, message: JsonRpcRequest) -> Any:
        self.last_request = message
        return self._response


_MISSING = object()


def _process(stdin: Any = _MISSING, stdout: Any = _MISSING) -> SimpleNamespace:
    return SimpleNamespace(
        stdin=object() if stdin is _MISSING else stdin,
        stdout=object() if stdout is _MISSING else stdout,
    )


def _initialize_result_payload() -> dict[str, Any]:
    return {
        "runtime": {
            "id": "runtime-1",
            "name": "kiln-runtime",
            "version": "0.1.0",
        },
        "protocol_version": get_args(DEFAULT_JSONRPC_VERSION)[0],
        "schema_set_version": SCHEMA_SET_VERSION,
        "compatibility_major": COMPATIBILITY_MAJOR,
        "supported_method_namespaces": ["runtime"],
        "supported_methods": ["runtime.initialize", "runtime.health"],
        "build": {
            "commit": "deadbeef",
            "date": "2026-06-30T00:00:00Z",
        },
    }


def _health_result_payload() -> dict[str, Any]:
    return {
        "initialized": True,
        "ready": True,
        "draining": False,
        "shutdown": False,
        "last_fatal_startup_error": None,
    }


def test_init_rejects_missing_stdin() -> None:
    with pytest.raises(RuntimeProcessError, match="stdin is unavailable"):
        RuntimeStdioConnection(_process(stdin=None))


def test_init_rejects_missing_stdout() -> None:
    with pytest.raises(RuntimeProcessError, match="stdout is unavailable"):
        RuntimeStdioConnection(_process(stdout=None))


@pytest.mark.anyio
async def test_initialize_returns_runtime_initialize_result(mocker) -> None:
    fake_peer = _FakePeer(
        JsonRpcSuccessResponse(id="1", result=_initialize_result_payload())
    )
    mocker.patch(
        "kiln.sdk.runtime_connection.BufferedByteReceiveStream", side_effect=lambda x: x
    )
    mocker.patch("kiln.sdk.runtime_connection.Peer", return_value=fake_peer)

    conn = RuntimeStdioConnection(_process())
    result = await conn.initialize()

    assert result.root.runtime.id == "runtime-1"
    assert fake_peer.last_request is not None
    assert fake_peer.last_request.method == "runtime.initialize"
    assert fake_peer.last_request.params is not None
    assert (
        fake_peer.last_request.params["protocol_version"]
        == get_args(DEFAULT_JSONRPC_VERSION)[0]
    )
    assert fake_peer.last_request.params["schema_set_version"] == SCHEMA_SET_VERSION
    assert fake_peer.last_request.params["compatibility_major"] == COMPATIBILITY_MAJOR
    assert fake_peer.last_request.params["client"] == {
        "name": PACKAGE_NAME,
        "version": __version__,
    }


@pytest.mark.anyio
async def test_initialize_raises_on_jsonrpc_error_response(mocker) -> None:
    fake_peer = _FakePeer(
        JsonRpcErrorResponse(
            id="1",
            error=JsonRpcErrorObject(code=-32000, message="boom", data=None),
        )
    )
    mocker.patch(
        "kiln.sdk.runtime_connection.BufferedByteReceiveStream", side_effect=lambda x: x
    )
    mocker.patch("kiln.sdk.runtime_connection.Peer", return_value=fake_peer)

    conn = RuntimeStdioConnection(_process())

    with pytest.raises(RuntimeProcessError, match=r"-32000 - boom"):
        await conn.initialize()


@pytest.mark.anyio
async def test_health_returns_runtime_health_result(mocker) -> None:
    fake_peer = _FakePeer(
        JsonRpcSuccessResponse(id="1", result=_health_result_payload())
    )
    mocker.patch(
        "kiln.sdk.runtime_connection.BufferedByteReceiveStream", side_effect=lambda x: x
    )
    mocker.patch("kiln.sdk.runtime_connection.Peer", return_value=fake_peer)

    conn = RuntimeStdioConnection(_process())
    result = await conn.health()

    assert result.root.ready is True
    assert fake_peer.last_request is not None
    assert fake_peer.last_request.method == "runtime.health"
    assert fake_peer.last_request.params is None


@pytest.mark.anyio
async def test_health_raises_on_unexpected_request_response(mocker) -> None:
    fake_peer = _FakePeer(JsonRpcRequest(id="1", method="runtime.initialize"))
    mocker.patch(
        "kiln.sdk.runtime_connection.BufferedByteReceiveStream", side_effect=lambda x: x
    )
    mocker.patch("kiln.sdk.runtime_connection.Peer", return_value=fake_peer)

    conn = RuntimeStdioConnection(_process())

    with pytest.raises(RuntimeProcessError, match="unexpected request"):
        await conn.health()
