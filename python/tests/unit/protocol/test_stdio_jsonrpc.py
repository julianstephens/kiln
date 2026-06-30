import json

import pytest
from anyio.streams.buffered import DelimiterNotFound, IncompleteRead

from kiln.protocol.errors import (
    JsonRpcFrameExceedsSizeLimitError,
    RuntimeStreamClosedError,
)
from kiln.protocol.jsonrpc import JsonRpcRequest, JsonRpcSuccessResponse
from kiln.protocol.stdio_jsonrpc import StdioJsonRpcPeer


class DummyStdin:
    def __init__(self) -> None:
        self.sent: list[bytes] = []

    async def send(self, payload: bytes) -> None:
        self.sent.append(payload)


class DummyStdout:
    def __init__(self, line: bytes | None = None, err: Exception | None = None) -> None:
        self._line = line
        self._err = err

    async def receive_until(self, _delimiter: bytes, _max_bytes: int) -> bytes:
        if self._err is not None:
            raise self._err
        if self._line is None:
            return b""
        return self._line


@pytest.mark.anyio
async def test_receive_decodes_line_into_typed_jsonrpc_message() -> None:
    raw = {
        "jsonrpc": "2.0",
        "id": "1",
        "result": {"ok": True},
    }
    peer = StdioJsonRpcPeer(
        stdin=DummyStdin(),
        stdout=DummyStdout(json.dumps(raw).encode()),  # type: ignore[arg-type]
    )

    msg = await peer.receive()

    assert isinstance(msg, JsonRpcSuccessResponse)
    assert msg.model_dump(mode="json") == raw


@pytest.mark.anyio
async def test_send_writes_exactly_one_newline_terminated_frame() -> None:
    stdin = DummyStdin()
    peer = StdioJsonRpcPeer(stdin=stdin, stdout=DummyStdout())  # type: ignore[arg-type]

    await peer.send(
        JsonRpcRequest(
            jsonrpc="2.0",
            id="1",
            method="repository.search",
            params={"query": "foo"},
        )
    )

    assert len(stdin.sent) == 1
    assert stdin.sent[0].endswith(b"\n")
    assert stdin.sent[0].count(b"\n") == 1


@pytest.mark.anyio
async def test_eof_maps_to_runtime_stream_closed_error() -> None:
    peer = StdioJsonRpcPeer(stdin=DummyStdin(), stdout=DummyStdout(b""))  # type: ignore[arg-type]

    with pytest.raises(RuntimeStreamClosedError):
        await peer.receive()


@pytest.mark.anyio
async def test_incomplete_read_maps_to_runtime_stream_closed_error() -> None:
    peer = StdioJsonRpcPeer(
        stdin=DummyStdin(),
        stdout=DummyStdout(err=IncompleteRead()),  # type: ignore[arg-type]
    )

    with pytest.raises(RuntimeStreamClosedError):
        await peer.receive()


@pytest.mark.anyio
async def test_delimiter_not_found_maps_to_frame_size_error() -> None:
    peer = StdioJsonRpcPeer(
        stdin=DummyStdin(),
        stdout=DummyStdout(err=DelimiterNotFound(128)),  # type: ignore[arg-type]
        max_message_bytes=128,
    )

    with pytest.raises(JsonRpcFrameExceedsSizeLimitError):
        await peer.receive()
