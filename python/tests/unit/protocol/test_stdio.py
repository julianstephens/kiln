import json

import pytest
from anyio.streams.buffered import DelimiterNotFound, IncompleteRead

from kiln.protocol.errors import (
    InvalidJsonRpcFrameError,
    JsonRpcFrameExceedsSizeLimitError,
    JsonRpcResponseIdMismatchError,
    RuntimeStreamClosedError,
    UnexpectedJsonRpcMessageError,
)
from kiln.protocol.jsonrpc import JsonRpcRequest, JsonRpcSuccessResponse
from kiln.protocol.stdio import Peer


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
    peer = Peer(
        stdin=DummyStdin(),  # type: ignore
        stdout=DummyStdout(json.dumps(raw).encode()),  # type: ignore[arg-type]
    )

    msg = await peer.receive()

    assert isinstance(msg, JsonRpcSuccessResponse)
    assert msg.model_dump(mode="json") == raw


@pytest.mark.anyio
async def test_send_writes_exactly_one_newline_terminated_frame() -> None:
    stdin = DummyStdin()
    peer = Peer(stdin=stdin, stdout=DummyStdout())  # type: ignore[arg-type]

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
    peer = Peer(stdin=DummyStdin(), stdout=DummyStdout(b""))  # type: ignore[arg-type]

    with pytest.raises(RuntimeStreamClosedError):
        await peer.receive()


@pytest.mark.anyio
async def test_incomplete_read_maps_to_runtime_stream_closed_error() -> None:
    peer = Peer(
        stdin=DummyStdin(),  # type: ignore
        stdout=DummyStdout(err=IncompleteRead()),  # type: ignore[arg-type]
    )

    with pytest.raises(RuntimeStreamClosedError):
        await peer.receive()


@pytest.mark.anyio
async def test_delimiter_not_found_maps_to_frame_size_error() -> None:
    peer = Peer(
        stdin=DummyStdin(),  # type: ignore
        stdout=DummyStdout(err=DelimiterNotFound(128)),  # type: ignore[arg-type]
        max_message_bytes=128,
    )

    with pytest.raises(JsonRpcFrameExceedsSizeLimitError):
        await peer.receive()


@pytest.mark.anyio
async def test_request_raises_on_response_id_mismatch() -> None:
    """Test that Peer.request() raises when response ID doesn't match request ID.

    This happens when we have a tracked pending request ID, but the response ID
    doesn't match the specific request that was sent.
    """
    stdin = DummyStdin()

    # Set up a scenario where we have multiple pending requests
    # and get a response with a different pending ID
    class MultiRequestStdout:
        def __init__(self) -> None:
            self.call_count = 0

        async def receive_until(self, _delimiter: bytes, _max_bytes: int) -> bytes:
            self.call_count += 1
            if self.call_count == 1:
                # Response has a different ID that's also pending
                response = JsonRpcSuccessResponse(id="999", result={"ok": True})
                return json.dumps(response.model_dump(mode="json")).encode()
            return b""

    request_msg = JsonRpcRequest(id="123", method="test.method")
    peer = Peer(stdin=stdin, stdout=MultiRequestStdout())  # type: ignore[arg-type]

    # Manually add another pending request so "999" exists in pending requests
    peer._pending_requests.add("999", "other.method")

    with pytest.raises(JsonRpcResponseIdMismatchError):
        await peer.request(request_msg)


@pytest.mark.anyio
async def test_request_raises_on_unknown_response_id() -> None:
    """Test that Peer.request() raises when response ID is not in pending requests."""
    stdin = DummyStdin()
    request_msg = JsonRpcRequest(id="123", method="test.method")

    # Response with ID that was never requested
    response = JsonRpcSuccessResponse(id="999", result={"ok": True})
    stdout = DummyStdout(json.dumps(response.model_dump(mode="json")).encode())

    peer = Peer(stdin=stdin, stdout=stdout)  # type: ignore[arg-type]

    with pytest.raises(UnexpectedJsonRpcMessageError):
        await peer.request(request_msg)


@pytest.mark.anyio
async def test_request_raises_on_unexpected_inbound_request() -> None:
    """Test that Peer.request() raises when receiving an inbound request instead of
    response."""
    stdin = DummyStdin()
    request_msg = JsonRpcRequest(id="123", method="test.method")

    # Inbound request instead of response
    inbound_request = JsonRpcRequest(id="456", method="remote.method")
    stdout = DummyStdout(json.dumps(inbound_request.model_dump(mode="json")).encode())

    peer = Peer(stdin=stdin, stdout=stdout)  # type: ignore[arg-type]

    with pytest.raises(UnexpectedJsonRpcMessageError):
        await peer.request(request_msg)


@pytest.mark.anyio
async def test_request_raises_on_null_response_id() -> None:
    """Test that Peer.request() rejects null/falsy response IDs during validation."""
    stdin = DummyStdin()
    request_msg = JsonRpcRequest(id="123", method="test.method")

    # Response with null ID triggers validation error during frame parsing
    response_data = {
        "jsonrpc": "2.0",
        "id": None,
        "result": {"ok": True},
    }
    stdout = DummyStdout(json.dumps(response_data).encode())

    peer = Peer(stdin=stdin, stdout=stdout)  # type: ignore[arg-type]

    # The validation error is raised during frame parsing, not in request()
    with pytest.raises(InvalidJsonRpcFrameError):
        await peer.request(request_msg)


@pytest.mark.anyio
async def test_request_cleans_up_pending_on_mismatch_error() -> None:
    """Test that pending requests are cleaned up even when response ID mismatches."""
    stdin = DummyStdin()

    class MultiRequestStdout:
        def __init__(self) -> None:
            self.call_count = 0

        async def receive_until(self, _delimiter: bytes, _max_bytes: int) -> bytes:
            self.call_count += 1
            if self.call_count == 1:
                response = JsonRpcSuccessResponse(id="999", result={"ok": True})
                return json.dumps(response.model_dump(mode="json")).encode()
            return b""

    request_msg = JsonRpcRequest(id="123", method="test.method")
    peer = Peer(stdin=stdin, stdout=MultiRequestStdout())  # type: ignore[arg-type]

    # Manually add another pending request so "999" exists
    peer._pending_requests.add("999", "other.method")

    with pytest.raises(JsonRpcResponseIdMismatchError):
        await peer.request(request_msg)

    # Verify pending requests are cleaned up
    assert "123" not in peer._pending_requests


@pytest.mark.anyio
async def test_request_cleans_up_pending_on_unexpected_message_error() -> None:
    """Test that pending requests are cleaned up when receiving unexpected message."""
    stdin = DummyStdin()
    request_msg = JsonRpcRequest(id="123", method="test.method")

    # Inbound request instead of response
    inbound_request = JsonRpcRequest(id="456", method="remote.method")
    stdout = DummyStdout(json.dumps(inbound_request.model_dump(mode="json")).encode())

    peer = Peer(stdin=stdin, stdout=stdout)  # type: ignore[arg-type]

    with pytest.raises(UnexpectedJsonRpcMessageError):
        await peer.request(request_msg)

    # Verify pending requests are cleaned up
    assert "123" not in peer._pending_requests


@pytest.mark.anyio
async def test_request_succeeds_with_matching_id() -> None:
    """Test that Peer.request() succeeds when response ID matches request ID."""
    stdin = DummyStdin()
    request_msg = JsonRpcRequest(id="123", method="test.method")

    # Response with matching ID
    response = JsonRpcSuccessResponse(id="123", result={"ok": True})
    stdout = DummyStdout(json.dumps(response.model_dump(mode="json")).encode())

    peer = Peer(stdin=stdin, stdout=stdout)  # type: ignore[arg-type]

    result = await peer.request(request_msg)

    assert isinstance(result, JsonRpcSuccessResponse)
    assert result.id == "123"
    assert result.result == {"ok": True}
    # Verify pending request was cleaned up
    assert "123" not in peer._pending_requests


@pytest.mark.anyio
async def test_request_sends_message_before_receiving() -> None:
    """Test that Peer.request() sends the request before waiting for response."""
    stdin = DummyStdin()
    request_msg = JsonRpcRequest(id="123", method="test.method", params={"foo": "bar"})

    response = JsonRpcSuccessResponse(id="123", result={"ok": True})
    stdout = DummyStdout(json.dumps(response.model_dump(mode="json")).encode())

    peer = Peer(stdin=stdin, stdout=stdout)  # type: ignore[arg-type]

    await peer.request(request_msg)

    # Verify request was sent
    assert len(stdin.sent) == 1
    assert stdin.sent[0].endswith(b"\n")
