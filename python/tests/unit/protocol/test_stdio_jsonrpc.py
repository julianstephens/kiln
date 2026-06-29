import json
from pathlib import Path

import pytest

from kiln.protocol.errors import (
    EmbeddedNewlineInMessageError,
    FramingError,
    InvalidJsonRpcFrameError,
    RuntimeStreamClosedError,
)
from kiln.protocol.framing import validate_frame
from kiln.protocol.stdio_jsonrpc import StdioJsonRpcPeer

FIXTURES_ROOT = (
    Path(__file__).resolve().parents[4] / "schemas" / "fixtures" / "valid" / "v1"
)


class DummyStdin:
    def __init__(self) -> None:
        self.sent: list[bytes] = []

    async def send(self, payload: bytes) -> None:
        self.sent.append(payload)


class DummyStdout:
    def __init__(self, line: bytes) -> None:
        self._line = line
        self.calls: list[tuple[bytes, int]] = []

    async def receive_until(self, delimiter: bytes, max_bytes: int) -> bytes:
        self.calls.append((delimiter, max_bytes))
        return self._line


class SequencedStdout:
    def __init__(self, lines: list[bytes]) -> None:
        self._lines = lines[:]
        self.calls: list[tuple[bytes, int]] = []

    async def receive_until(self, delimiter: bytes, max_bytes: int) -> bytes:
        self.calls.append((delimiter, max_bytes))
        if not self._lines:
            return b""
        return self._lines.pop(0)


def _load_fixture(name: str) -> dict:
    return json.loads((FIXTURES_ROOT / name).read_text())


def _valid_repository_search_success_response_frame() -> bytes:
    payload = _load_fixture("repository-search-result-basic.json")
    return json.dumps(
        {
            "jsonrpc": "2.0",
            "id": "req-1",
            "method": "repository.search",
            "result": payload,
        }
    ).encode()


def _valid_repository_search_error_response_frame() -> bytes:
    payload = _load_fixture("repository-error-basic.json")
    return json.dumps(
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


@pytest.mark.anyio
async def test_read_frame_returns_validated_jsonrpc_frame_bytes() -> None:
    payload = _valid_repository_search_success_response_frame()
    stdin = DummyStdin()
    stdout = DummyStdout(payload)
    peer = StdioJsonRpcPeer(stdin=stdin, stdout=stdout)  # type: ignore

    frame = await peer.receive()
    expected = validate_frame(payload)
    expected.pop("method", None)

    assert stdout.calls == [(b"\n", peer._max_message_bytes)]
    assert frame.model_dump(mode="json") == expected


@pytest.mark.anyio
async def test_read_frame_rejects_embedded_newline() -> None:
    peer = StdioJsonRpcPeer(stdin=DummyStdin(), stdout=DummyStdout(b'{"x":1}\n'))  # type: ignore

    with pytest.raises(EmbeddedNewlineInMessageError):
        await peer.receive()


@pytest.mark.anyio
async def test_read_frame_raises_on_closed_stream() -> None:
    peer = StdioJsonRpcPeer(stdin=DummyStdin(), stdout=DummyStdout(b""))  # type: ignore

    with pytest.raises(RuntimeStreamClosedError):
        await peer.receive()


@pytest.mark.anyio
async def test_read_frame_rejects_truncated_json() -> None:
    truncated = b'{"jsonrpc":"2.0","id":"1","method":"repository.search","params":'
    peer = StdioJsonRpcPeer(stdin=DummyStdin(), stdout=DummyStdout(truncated))  # type: ignore

    with pytest.raises(FramingError, match="invalid JSON-RPC frame"):
        await peer.receive()


@pytest.mark.anyio
async def test_read_frame_reads_multiple_frames_in_sequence() -> None:
    success = _valid_repository_search_success_response_frame()
    error = _valid_repository_search_error_response_frame()
    stdout = SequencedStdout([success, error])
    peer = StdioJsonRpcPeer(stdin=DummyStdin(), stdout=stdout)  # type: ignore

    first = await peer.receive()
    second = await peer.receive()
    expected_success = validate_frame(success)
    expected_success.pop("method", None)
    expected_error = validate_frame(error)
    expected_error.pop("method", None)

    assert first.model_dump(mode="json") == expected_success
    assert second.model_dump(mode="json") == expected_error
    assert stdout.calls == [
        (b"\n", peer._max_message_bytes),
        (b"\n", peer._max_message_bytes),
    ]


@pytest.mark.anyio
async def test_send_frame_validates_and_writes_single_line_json() -> None:
    payload = json.dumps(
        {
            "jsonrpc": "2.0",
            "id": "req-1",
            "method": "repository.search",
            "params": _load_fixture("repository-search-request-payload-basic.json"),
        }
    ).encode()
    stdin = DummyStdin()
    peer = StdioJsonRpcPeer(stdin=stdin, stdout=DummyStdout(b"unused"))  # type: ignore

    await peer.send(payload)

    assert len(stdin.sent) == 1
    assert stdin.sent[0].endswith(b"\n")
    assert b"\n" not in stdin.sent[0][:-1]
    assert json.loads(stdin.sent[0][:-1].decode()) == validate_frame(payload)


@pytest.mark.anyio
async def test_receive_rejects_request_frame() -> None:
    request = json.dumps(
        {
            "jsonrpc": "2.0",
            "id": "req-1",
            "method": "repository.search",
            "params": _load_fixture("repository-search-request-payload-basic.json"),
        }
    ).encode()
    peer = StdioJsonRpcPeer(stdin=DummyStdin(), stdout=DummyStdout(request))  # type: ignore

    with pytest.raises(InvalidJsonRpcFrameError, match="without 'result' or 'error'"):
        await peer.receive()


@pytest.mark.anyio
async def test_send_frame_rejects_embedded_newline() -> None:
    peer = StdioJsonRpcPeer(stdin=DummyStdin(), stdout=DummyStdout(b"unused"))  # type: ignore

    with pytest.raises(EmbeddedNewlineInMessageError):
        await peer.send(b'{"jsonrpc":"2.0"}\n')
