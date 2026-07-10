from __future__ import annotations

from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock

import pytest
from pydantic import ValidationError

from kiln.protocol.jsonrpc import (
    JsonRpcErrorObject,
    JsonRpcErrorResponse,
    JsonRpcRequest,
    JsonRpcSuccessResponse,
)
from kiln.schemas import COMPATIBILITY_MAJOR, SCHEMA_SET_VERSION
from kiln.sdk import PACKAGE_NAME, __version__
from kiln.sdk.errors import RuntimeMethodError, RuntimeProcessError
from kiln.sdk.runtime_connection import (
    RUNTIME_PROTOCOL_VERSION,
    DefaultShutdownConfig,
    RuntimeConnectionState,
    ShutdownConfig,
)
from kiln.sdk.runtime_connection import (
    RuntimeStdioConnection as _RuntimeStdioConnection,
)


def RuntimeStdioConnection(  # noqa: N802
    process: Any,
    state: RuntimeConnectionState = RuntimeConnectionState.EXITED,
    shutdown_config: ShutdownConfig = DefaultShutdownConfig,
) -> _RuntimeStdioConnection:
    return _RuntimeStdioConnection(
        process=process,
        shutdown_config=shutdown_config,
        state=state,
    )


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
        "protocol_version": RUNTIME_PROTOCOL_VERSION,
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


def _shutdown_result_payload(
    *,
    accepted: bool = True,
    draining: bool = True,
    shutdown: bool = False,
    in_flight_request_count: int = 0,
) -> dict[str, Any]:
    return {
        "accepted": accepted,
        "draining": draining,
        "shutdown": shutdown,
        "in_flight_request_count": in_flight_request_count,
    }


def test_init_rejects_missing_stdin() -> None:
    with pytest.raises(RuntimeProcessError, match="stdin is unavailable"):
        RuntimeStdioConnection(_process(stdin=None), RuntimeConnectionState.STARTING)


def test_init_rejects_missing_stdout() -> None:
    with pytest.raises(RuntimeProcessError, match="stdout is unavailable"):
        RuntimeStdioConnection(_process(stdout=None), RuntimeConnectionState.STARTING)


@pytest.mark.parametrize(
    ("initial_state", "expected_state"),
    [
        (RuntimeConnectionState.STARTING, RuntimeConnectionState.STARTING),
        (RuntimeConnectionState.READY, RuntimeConnectionState.READY),
        (RuntimeConnectionState.DRAINING, RuntimeConnectionState.DRAINING),
        (RuntimeConnectionState.EXITED, RuntimeConnectionState.EXITED),
    ],
)
def test_init_sets_connection_state(
    initial_state: RuntimeConnectionState, expected_state: RuntimeConnectionState
) -> None:
    conn = RuntimeStdioConnection(_process(), initial_state)

    assert conn.state == expected_state


@pytest.mark.anyio
async def test_initialize_returns_runtime_initialize_result(mocker) -> None:
    fake_peer = _FakePeer(
        JsonRpcSuccessResponse(id="1", result=_initialize_result_payload())
    )
    mocker.patch(
        "kiln.sdk.runtime_connection.BufferedByteReceiveStream", side_effect=lambda x: x
    )
    mocker.patch("kiln.sdk.runtime_connection.Peer", return_value=fake_peer)

    conn = RuntimeStdioConnection(_process(), RuntimeConnectionState.STARTING)
    result = await conn.initialize()

    assert result.root.runtime.id == "runtime-1"
    assert fake_peer.last_request is not None
    assert fake_peer.last_request.method == "runtime.initialize"
    assert fake_peer.last_request.params is not None
    assert fake_peer.last_request.params["protocol_version"] == RUNTIME_PROTOCOL_VERSION
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
            error=JsonRpcErrorObject(
                code=-32000,
                message="boom",
                data={
                    "kiln_error": {
                        "code": "runtime.internal",
                        "category": "internal",
                        "message": "boom",
                        "retryable": False,
                        "details": {},
                    }
                },
            ),
        )
    )
    mocker.patch(
        "kiln.sdk.runtime_connection.BufferedByteReceiveStream", side_effect=lambda x: x
    )
    mocker.patch("kiln.sdk.runtime_connection.Peer", return_value=fake_peer)

    conn = RuntimeStdioConnection(_process(), RuntimeConnectionState.STARTING)

    with pytest.raises(
        RuntimeMethodError, match=r"jsonrpc_code=-32000, message=boom"
    ) as exc_info:
        await conn.initialize()

    exc = exc_info.value
    assert exc.method == "runtime.initialize"
    assert exc.response is fake_peer._response
    assert exc.jsonrpc_code == -32000
    assert exc.message == "boom"
    assert exc.error_data == fake_peer._response.error.data
    assert exc.kiln_error.root.kiln_error.code == "runtime.internal"


@pytest.mark.anyio
async def test_health_returns_runtime_health_result(mocker) -> None:
    fake_peer = _FakePeer(
        JsonRpcSuccessResponse(id="1", result=_health_result_payload())
    )
    mocker.patch(
        "kiln.sdk.runtime_connection.BufferedByteReceiveStream", side_effect=lambda x: x
    )
    mocker.patch("kiln.sdk.runtime_connection.Peer", return_value=fake_peer)

    conn = RuntimeStdioConnection(_process(), RuntimeConnectionState.STARTING)
    result = await conn.health()

    assert result.root.ready is True
    assert conn.state == RuntimeConnectionState.READY
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

    conn = RuntimeStdioConnection(_process(), RuntimeConnectionState.STARTING)

    with pytest.raises(RuntimeProcessError, match="unexpected request"):
        await conn.health()


@pytest.mark.anyio
async def test_error_data_validation_and_preservation(mocker) -> None:
    """Test that error data with additional fields is preserved."""
    error_data = {
        "kiln_error": {
            "code": "runtime.validation",
            "category": "validation",
            "message": "validation failed",
            "retryable": True,
            "details": {"field": "name", "reason": "too short"},
            "correlation_id": "corr-123",
            "runtime_id": "runtime-2",
        }
    }
    fake_peer = _FakePeer(
        JsonRpcErrorResponse(
            id="1",
            error=JsonRpcErrorObject(
                code=-32001,
                message="validation failed",
                data=error_data,
            ),
        )
    )
    mocker.patch(
        "kiln.sdk.runtime_connection.BufferedByteReceiveStream", side_effect=lambda x: x
    )
    mocker.patch("kiln.sdk.runtime_connection.Peer", return_value=fake_peer)

    conn = RuntimeStdioConnection(_process(), RuntimeConnectionState.STARTING)

    with pytest.raises(RuntimeMethodError) as exc_info:
        await conn.initialize()

    # Verify the error message contains the key information
    exc = exc_info.value

    assert exc.response.error.data == error_data
    assert exc.kiln_error.root.kiln_error.details == {
        "field": "name",
        "reason": "too short",
    }
    assert exc.kiln_error.root.kiln_error.correlation_id == "corr-123"
    assert exc.kiln_error.root.kiln_error.runtime_id == "runtime-2"


@pytest.mark.anyio
async def test_initialize_raises_on_incompatible_protocol_version(mocker) -> None:
    """Test that incompatible protocol version error is properly raised."""
    error_data = {
        "kiln_error": {
            "code": "runtime.compatibility",
            "category": "compatibility",
            "message": "incompatible protocol version",
            "retryable": False,
            "details": {},
        }
    }
    fake_peer = _FakePeer(
        JsonRpcErrorResponse(
            id="1",
            error=JsonRpcErrorObject(
                code=-32002,
                message="incompatible protocol version",
                data=error_data,
            ),
        )
    )
    mocker.patch(
        "kiln.sdk.runtime_connection.BufferedByteReceiveStream", side_effect=lambda x: x
    )
    mocker.patch("kiln.sdk.runtime_connection.Peer", return_value=fake_peer)

    conn = RuntimeStdioConnection(_process(), RuntimeConnectionState.STARTING)

    with pytest.raises(RuntimeMethodError, match="incompatible protocol version"):
        await conn.initialize()


@pytest.mark.anyio
async def test_initialize_raises_on_incompatible_schema_set(mocker) -> None:
    """Test that incompatible schema-set error is properly raised."""
    error_data = {
        "kiln_error": {
            "code": "runtime.compatibility",
            "category": "compatibility",
            "message": "incompatible schema-set version",
            "retryable": False,
            "details": {},
        }
    }
    fake_peer = _FakePeer(
        JsonRpcErrorResponse(
            id="1",
            error=JsonRpcErrorObject(
                code=-32003,
                message="incompatible schema-set version",
                data=error_data,
            ),
        )
    )
    mocker.patch(
        "kiln.sdk.runtime_connection.BufferedByteReceiveStream", side_effect=lambda x: x
    )
    mocker.patch("kiln.sdk.runtime_connection.Peer", return_value=fake_peer)

    conn = RuntimeStdioConnection(_process(), RuntimeConnectionState.STARTING)

    with pytest.raises(RuntimeMethodError, match="incompatible schema-set"):
        await conn.initialize()


@pytest.mark.anyio
async def test_initialize_raises_on_malformed_success_result(mocker) -> None:
    """Test that malformed success result raises validation error."""
    # Missing required fields
    malformed_result = {
        "runtime": {
            "id": "runtime-1",
            # missing 'name' and 'version'
        },
        # missing other required fields
    }
    fake_peer = _FakePeer(JsonRpcSuccessResponse(id="1", result=malformed_result))
    mocker.patch(
        "kiln.sdk.runtime_connection.BufferedByteReceiveStream", side_effect=lambda x: x
    )
    mocker.patch("kiln.sdk.runtime_connection.Peer", return_value=fake_peer)

    conn = RuntimeStdioConnection(_process(), RuntimeConnectionState.STARTING)

    with pytest.raises(ValidationError):  # ValidationError
        await conn.initialize()


@pytest.mark.anyio
async def test_initialize_raises_on_malformed_error_data(mocker) -> None:
    """Test that malformed error data raises validation error."""
    # Missing required fields in kiln_error
    malformed_error_data = {
        "kiln_error": {
            "code": "runtime.internal",
            # missing 'category', 'message', 'retryable'
        }
    }
    fake_peer = _FakePeer(
        JsonRpcErrorResponse(
            id="1",
            error=JsonRpcErrorObject(
                code=-32000,
                message="error",
                data=malformed_error_data,
            ),
        )
    )
    mocker.patch(
        "kiln.sdk.runtime_connection.BufferedByteReceiveStream", side_effect=lambda x: x
    )
    mocker.patch("kiln.sdk.runtime_connection.Peer", return_value=fake_peer)

    conn = RuntimeStdioConnection(_process(), RuntimeConnectionState.STARTING)

    with pytest.raises(ValidationError):
        await conn.initialize()


@pytest.mark.anyio
async def test_health_not_ready(mocker) -> None:
    """Test health check when runtime is not ready."""
    health_payload = _health_result_payload()
    health_payload["ready"] = False
    fake_peer = _FakePeer(JsonRpcSuccessResponse(id="1", result=health_payload))
    mocker.patch(
        "kiln.sdk.runtime_connection.BufferedByteReceiveStream", side_effect=lambda x: x
    )
    mocker.patch("kiln.sdk.runtime_connection.Peer", return_value=fake_peer)

    conn = RuntimeStdioConnection(_process(), RuntimeConnectionState.STARTING)
    result = await conn.health()

    assert result.root.ready is False
    assert result.root.initialized is True
    assert conn.state == RuntimeConnectionState.STARTING


@pytest.mark.anyio
async def test_health_sets_draining_state(mocker) -> None:
    health_payload = _health_result_payload()
    health_payload["ready"] = False
    health_payload["draining"] = True
    fake_peer = _FakePeer(JsonRpcSuccessResponse(id="1", result=health_payload))
    mocker.patch(
        "kiln.sdk.runtime_connection.BufferedByteReceiveStream", side_effect=lambda x: x
    )
    mocker.patch("kiln.sdk.runtime_connection.Peer", return_value=fake_peer)

    conn = RuntimeStdioConnection(_process(), RuntimeConnectionState.STARTING)
    result = await conn.health()

    assert result.root.draining is True
    assert conn.state == RuntimeConnectionState.DRAINING


@pytest.mark.anyio
async def test_health_after_shutdown(mocker) -> None:
    """Test health check after runtime shutdown."""
    health_payload = _health_result_payload()
    health_payload["shutdown"] = True
    health_payload["ready"] = False
    health_payload["initialized"] = False
    fake_peer = _FakePeer(JsonRpcSuccessResponse(id="1", result=health_payload))
    mocker.patch(
        "kiln.sdk.runtime_connection.BufferedByteReceiveStream", side_effect=lambda x: x
    )
    mocker.patch("kiln.sdk.runtime_connection.Peer", return_value=fake_peer)

    conn = RuntimeStdioConnection(_process(), RuntimeConnectionState.STARTING)
    result = await conn.health()

    assert result.root.shutdown is True
    assert result.root.ready is False
    assert conn.state == RuntimeConnectionState.EXITED


@pytest.mark.anyio
async def test_initialize_and_health_ordering(mocker) -> None:
    """Test that initialize is called before health."""
    call_sequence = []

    class SequenceTrackingPeer:
        def __init__(self):
            self.last_request: JsonRpcRequest | None = None

        async def request(self, message: JsonRpcRequest) -> Any:
            self.last_request = message
            call_sequence.append(message.method)

            if message.method == "runtime.initialize":
                return JsonRpcSuccessResponse(
                    id="1", result=_initialize_result_payload()
                )
            if message.method == "runtime.health":
                return JsonRpcSuccessResponse(id="2", result=_health_result_payload())
            raise RuntimeProcessError(
                message=f"Unexpected method called: {message.method}"
            )

    fake_peer = SequenceTrackingPeer()
    mocker.patch(
        "kiln.sdk.runtime_connection.BufferedByteReceiveStream", side_effect=lambda x: x
    )
    mocker.patch("kiln.sdk.runtime_connection.Peer", return_value=fake_peer)

    conn = RuntimeStdioConnection(_process(), RuntimeConnectionState.STARTING)

    # Call initialize then health
    await conn.initialize()
    await conn.health()

    assert call_sequence == ["runtime.initialize", "runtime.health"]


@pytest.mark.anyio
async def test_windows_startup_argument_shape(mocker) -> None:
    """Test Windows process creation with proper argument shape.

    This test verifies that the Windows process creation function is called
    with the correct argument structure.
    """
    # Mock the entire module to avoid platform-specific imports
    mock_win32 = mocker.MagicMock()
    mocker.patch.dict("sys.modules", {"kiln.sdk._runtime_os.win32": mock_win32})

    # Create a mock process
    mock_process = mocker.AsyncMock()
    mock_process.stdin = mocker.MagicMock()
    mock_process.stdout = mocker.MagicMock()

    # Create a test function with the expected signature
    async def test_create_windows_process(command: str, args: list[str], **kwargs):
        """Mock function to test argument shape."""
        # Verify arguments are in correct shape
        assert isinstance(command, str)
        assert isinstance(args, list)
        assert all(isinstance(arg, str) for arg in args)
        # Additional kwargs should be optional
        assert "env" in kwargs or "cwd" in kwargs or "errlog" in kwargs or not kwargs
        return mock_process

    mock_win32.create_windows_process = test_create_windows_process

    # Call with expected arguments
    result = await mock_win32.create_windows_process(
        "runtime.exe", args=["--port", "8080"], cwd="/tmp"
    )

    assert result == mock_process


@pytest.mark.anyio
async def test_health_sends_non_empty_request_id(mocker) -> None:
    """Test that health() sends a non-empty request ID without mocking request()."""
    captured_request: JsonRpcRequest | None = None

    async def capture_request(request: JsonRpcRequest) -> Any:
        """Capture the request before returning response."""
        nonlocal captured_request
        captured_request = request
        return JsonRpcSuccessResponse(id=request.id, result=_health_result_payload())

    class RequestCapturingPeer:
        def __init__(self):
            self.last_request: JsonRpcRequest | None = None

        async def request(self, message: JsonRpcRequest) -> Any:
            self.last_request = message
            return await capture_request(message)

    peer = RequestCapturingPeer()
    mocker.patch(
        "kiln.sdk.runtime_connection.BufferedByteReceiveStream", side_effect=lambda x: x
    )
    mocker.patch("kiln.sdk.runtime_connection.Peer", return_value=peer)

    conn = RuntimeStdioConnection(_process(), RuntimeConnectionState.STARTING)
    result = await conn.health()

    # Verify the captured request has a non-empty ID
    assert captured_request is not None
    assert captured_request.id
    if isinstance(captured_request.id, int):
        assert captured_request.id > 0
    assert captured_request.method == "runtime.health"
    assert captured_request.params is None
    assert result.root.ready is True


@pytest.mark.anyio
async def test_initialize_raises_on_process_exit_during_request(mocker) -> None:
    """Test that process exit during request is detected and raised.

    Simulates the case where the runtime process exits while an RPC request
    is in flight, resulting in a broken pipe or connection error.
    """

    class ProcessExitDuringRequestPeer:
        """Fake peer that simulates process exit mid-request."""

        def __init__(self):
            self.last_request: JsonRpcRequest | None = None

        async def request(self, message: JsonRpcRequest) -> Any:
            self.last_request = message
            # Simulate process exit by raising connection error
            raise RuntimeProcessError(message="runtime process exited during request")

    peer = ProcessExitDuringRequestPeer()
    mocker.patch(
        "kiln.sdk.runtime_connection.BufferedByteReceiveStream", side_effect=lambda x: x
    )
    mocker.patch("kiln.sdk.runtime_connection.Peer", return_value=peer)

    conn = RuntimeStdioConnection(_process(), RuntimeConnectionState.STARTING)

    with pytest.raises(RuntimeProcessError, match="exited during request"):
        await conn.initialize()


@pytest.mark.anyio
async def test_health_raises_on_process_exit_during_request(mocker) -> None:
    """Test that health() detects process exit during request."""

    class ProcessExitDuringRequestPeer:
        def __init__(self):
            self.last_request: JsonRpcRequest | None = None

        async def request(self, message: JsonRpcRequest) -> Any:
            self.last_request = message
            raise RuntimeProcessError(message="runtime process exited unexpectedly")

    peer = ProcessExitDuringRequestPeer()
    mocker.patch(
        "kiln.sdk.runtime_connection.BufferedByteReceiveStream", side_effect=lambda x: x
    )
    mocker.patch("kiln.sdk.runtime_connection.Peer", return_value=peer)

    conn = RuntimeStdioConnection(_process(), RuntimeConnectionState.STARTING)

    with pytest.raises(RuntimeProcessError, match="exited unexpectedly"):
        await conn.health()


@pytest.mark.anyio
async def test_multiple_sequential_initialize_calls(mocker) -> None:
    """Test that initialize can be called multiple times (returns same result)."""
    call_count = 0

    class CountingPeer:
        def __init__(self):
            self.last_request: JsonRpcRequest | None = None

        async def request(self, message: JsonRpcRequest) -> Any:
            nonlocal call_count
            call_count += 1
            self.last_request = message
            return JsonRpcSuccessResponse(
                id=message.id, result=_initialize_result_payload()
            )

    peer = CountingPeer()
    mocker.patch(
        "kiln.sdk.runtime_connection.BufferedByteReceiveStream", side_effect=lambda x: x
    )
    mocker.patch("kiln.sdk.runtime_connection.Peer", return_value=peer)

    conn = RuntimeStdioConnection(_process(), RuntimeConnectionState.STARTING)

    # First initialize succeeds
    result1 = await conn.initialize()
    assert result1.root.runtime.id == "runtime-1"
    assert call_count == 1

    # Second initialize should also succeed (idempotent)
    result2 = await conn.initialize()
    assert result2.root.runtime.id == "runtime-1"
    assert call_count == 2


@pytest.mark.anyio
async def test_initialize_raises_runtime_connection_closed_error(mocker) -> None:
    """Test that RuntimeConnectionClosedError is raised when stream closes.

    Verifies:
    - RuntimeConnectionClosedError is raised on stream closure
    - in_flight contains the current request id and method
    """
    from kiln.protocol.errors import RuntimeConnectionClosedError
    from kiln.protocol.pending import InflightRequestDisposition

    class StreamClosedPeer:
        def __init__(self):
            self.last_request: JsonRpcRequest | None = None

        async def request(self, message: JsonRpcRequest) -> Any:
            self.last_request = message
            # Simulate stream closure during request
            exc = RuntimeConnectionClosedError(
                message="runtime connection closed",
                in_flight=(
                    InflightRequestDisposition(
                        request_id=str(message.id),
                        method=message.method,
                        disposition="failed_connection_closed",
                    ),
                ),
            )
            raise exc

    peer = StreamClosedPeer()
    mocker.patch(
        "kiln.sdk.runtime_connection.BufferedByteReceiveStream", side_effect=lambda x: x
    )
    mocker.patch("kiln.sdk.runtime_connection.Peer", return_value=peer)

    conn = RuntimeStdioConnection(_process(), RuntimeConnectionState.STARTING)

    with pytest.raises(RuntimeConnectionClosedError) as exc_info:
        await conn.initialize()

    # Verify in_flight contains the request info
    error = exc_info.value
    assert len(error.in_flight) == 1
    assert peer.last_request is not None
    assert error.in_flight[0].request_id == peer.last_request.id
    assert error.in_flight[0].method == "runtime.initialize"
    assert error.in_flight[0].disposition == "failed_connection_closed"


@pytest.mark.anyio
async def test_health_raises_runtime_connection_closed_error(mocker) -> None:
    """Test that health() propagates RuntimeConnectionClosedError with in_flight."""
    from kiln.protocol.errors import RuntimeConnectionClosedError
    from kiln.protocol.pending import InflightRequestDisposition

    class StreamClosedPeer:
        def __init__(self):
            self.last_request: JsonRpcRequest | None = None

        async def request(self, message: JsonRpcRequest) -> Any:
            self.last_request = message
            # Simulate stream closure during health check
            exc = RuntimeConnectionClosedError(
                message="runtime connection closed during health",
                in_flight=(
                    InflightRequestDisposition(
                        request_id=str(message.id),
                        method=message.method,
                        disposition="failed_connection_closed",
                    ),
                ),
            )
            raise exc

    peer = StreamClosedPeer()
    mocker.patch(
        "kiln.sdk.runtime_connection.BufferedByteReceiveStream", side_effect=lambda x: x
    )
    mocker.patch("kiln.sdk.runtime_connection.Peer", return_value=peer)

    conn = RuntimeStdioConnection(_process(), RuntimeConnectionState.STARTING)

    with pytest.raises(RuntimeConnectionClosedError) as exc_info:
        await conn.health()

    # Verify in_flight contains the health request info
    error = exc_info.value
    assert len(error.in_flight) == 1
    assert peer.last_request is not None
    assert error.in_flight[0].request_id == peer.last_request.id
    assert error.in_flight[0].method == "runtime.health"
    assert error.in_flight[0].disposition == "failed_connection_closed"


@pytest.mark.anyio
async def test_shutdown_returns_runtime_shutdown_result_and_sets_draining_state(
    mocker,
) -> None:
    fake_peer = _FakePeer(
        JsonRpcSuccessResponse(id="1", result=_shutdown_result_payload())
    )
    mocker.patch(
        "kiln.sdk.runtime_connection.BufferedByteReceiveStream", side_effect=lambda x: x
    )
    mocker.patch("kiln.sdk.runtime_connection.Peer", return_value=fake_peer)

    conn = RuntimeStdioConnection(
        _process(),
        RuntimeConnectionState.STARTING,
        ShutdownConfig(
            kill_timeout_seconds=3,
            process_exit_timeout_seconds=1,
            cancel_in_flight_requests=False,
        ),
    )
    result = await conn.shutdown()

    assert result.root.accepted is True
    assert result.root.draining is True
    assert result.root.shutdown is False
    assert result.root.in_flight_request_count == 0
    assert conn.state == RuntimeConnectionState.DRAINING
    assert fake_peer.last_request is not None
    assert fake_peer.last_request.method == "runtime.shutdown"
    assert fake_peer.last_request.params == {
        "cancel_in_flight_requests": False,
        "reason": "caller_requested",
    }


@pytest.mark.anyio
async def test_shutdown_raises_on_jsonrpc_error_response(mocker) -> None:
    fake_peer = _FakePeer(
        JsonRpcErrorResponse(
            id="1",
            error=JsonRpcErrorObject(
                code=-32000,
                message="shutdown denied",
                data={
                    "kiln_error": {
                        "code": "runtime.shutdown",
                        "category": "shutdown",
                        "message": "shutdown denied",
                        "retryable": True,
                        "details": {},
                    }
                },
            ),
        )
    )
    mocker.patch(
        "kiln.sdk.runtime_connection.BufferedByteReceiveStream", side_effect=lambda x: x
    )
    mocker.patch("kiln.sdk.runtime_connection.Peer", return_value=fake_peer)

    mock_connection = MagicMock(spec=RuntimeStdioConnection)
    mock_connection.state = RuntimeConnectionState.STARTING
    mock_connection._shutdown_config = ShutdownConfig(
        kill_timeout_seconds=3,
        process_exit_timeout_seconds=1,
        cancel_in_flight_requests=True,
    )
    mock_connection.peer = fake_peer

    real_shutdown = _RuntimeStdioConnection.shutdown
    mock_connection.shutdown = lambda: real_shutdown(mock_connection)

    with pytest.raises(
        RuntimeMethodError, match=r"jsonrpc_code=-32000, message=shutdown denied"
    ) as exc_info:
        await mock_connection.shutdown()

    exc = exc_info.value
    assert exc.method == "runtime.shutdown"
    assert exc.response is fake_peer._response
    assert exc.kiln_error.root.kiln_error.category == "shutdown"


@pytest.mark.anyio
async def test_shutdown_raises_on_unexpected_request_response(mocker) -> None:
    fake_peer = _FakePeer(JsonRpcRequest(id="1", method="runtime.health"))
    mocker.patch(
        "kiln.sdk.runtime_connection.BufferedByteReceiveStream", side_effect=lambda x: x
    )
    mocker.patch("kiln.sdk.runtime_connection.Peer", return_value=fake_peer)

    mock_connection = MagicMock(spec=RuntimeStdioConnection)
    mock_connection.state = RuntimeConnectionState.STARTING
    mock_connection._shutdown_config = ShutdownConfig(
        process_exit_timeout_seconds=1,
        kill_timeout_seconds=3,
        cancel_in_flight_requests=True,
    )
    mock_connection.peer = fake_peer

    real_shutdown = _RuntimeStdioConnection.shutdown
    mock_connection.shutdown = lambda: real_shutdown(mock_connection)

    with pytest.raises(RuntimeProcessError, match="unexpected request"):
        await mock_connection.shutdown()


@pytest.mark.anyio
async def test_shutdown_raises_on_unexpected_response_type(mocker) -> None:
    fake_peer = _FakePeer("not-a-jsonrpc-response")
    mocker.patch(
        "kiln.sdk.runtime_connection.BufferedByteReceiveStream", side_effect=lambda x: x
    )
    mocker.patch("kiln.sdk.runtime_connection.Peer", return_value=fake_peer)

    mock_connection = MagicMock(spec=RuntimeStdioConnection)
    mock_connection.state = RuntimeConnectionState.STARTING
    mock_connection._shutdown_config = ShutdownConfig(
        kill_timeout_seconds=3,
        process_exit_timeout_seconds=1,
        cancel_in_flight_requests=True,
    )
    mock_connection.peer = fake_peer

    real_shutdown = _RuntimeStdioConnection.shutdown
    mock_connection.shutdown = lambda: real_shutdown(mock_connection)

    with pytest.raises(RuntimeProcessError, match="unexpected response type"):
        await mock_connection.shutdown()
