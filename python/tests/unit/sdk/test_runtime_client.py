"""Integration tests for RuntimeClient startup and lifecycle."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any
from unittest.mock import AsyncMock, MagicMock, PropertyMock

import pytest

from kiln.protocol.errors import RuntimeConnectionClosedError
from kiln.protocol.jsonrpc import JsonRpcRequest
from kiln.protocol.pending import InflightRequestDisposition
from kiln.sdk.errors import RuntimeProcessExitedError
from kiln.sdk.runtime_client import RuntimeClient
from kiln.sdk.runtime_connection import RuntimeStdioConnection
from kiln.sdk.runtime_exit import RuntimeExitStatus, StderrTailBuffer


@pytest.mark.anyio
async def test_start_raises_runtime_process_exited_error_on_connection_closed(
    mocker,
) -> None:
    """Test RuntimeClient.start raises RuntimeProcessExitedError on connection closed.

    Verifies:
    - RuntimeProcess with non-zero returncode and stderr_tail is captured
    - RuntimeConnectionClosedError with in_flight is propagated
    - RuntimeProcessExitedError contains exit_status and in_flight info
    """
    # Create a fake process with returncode=1 and stderr_tail containing "boom"
    stderr_tail = StderrTailBuffer()
    stderr_tail.append(b"boom")

    fake_process = SimpleNamespace(
        stdin=object(),
        stdout=object(),
        stderr=None,
        returncode=1,
    )

    # Create a mock RuntimeProcess with the proper structure
    fake_runtime_process = MagicMock()
    fake_runtime_process.process = fake_process
    fake_runtime_process.is_alive = False
    fake_runtime_process.exit_status = RuntimeExitStatus(
        expected=False,
        returncode=1,
        signal=None,
        stderr_tail="boom",
    )
    # Add the stderr_tail property
    type(fake_runtime_process).stderr_tail = PropertyMock(return_value=stderr_tail)
    # Mock aclose to be async
    fake_runtime_process.aclose = AsyncMock()

    # Mock RuntimeProcess.start to return our fake process
    mocker.patch(
        "kiln.sdk.runtime_client.RuntimeProcess.start",
        new_callable=AsyncMock,
        return_value=fake_runtime_process,
    )

    # Create a fake peer that raises RuntimeConnectionClosedError on initialize
    class ConnectionClosedPeer:
        def __init__(self):
            self.last_request: JsonRpcRequest | None = None

        async def request(self, message: JsonRpcRequest) -> Any:
            self.last_request = message
            # Simulate connection closed during initialize with in_flight tracking
            raise RuntimeConnectionClosedError(
                message="connection closed",
                in_flight=(
                    InflightRequestDisposition(
                        request_id=str(message.id),
                        method=message.method,
                        disposition="failed_connection_closed",
                    ),
                ),
            )

    ConnectionClosedPeer()

    # Mock RuntimeStdioConnection to use our connection closed peer
    mock_connection = MagicMock(spec=RuntimeStdioConnection)
    mock_connection.process = fake_process
    mock_connection.state = "starting"
    mock_connection.mark_failed = MagicMock()
    mock_connection.drain_stderr = AsyncMock()

    # Set up initialize to raise RuntimeConnectionClosedError
    mock_connection.initialize = AsyncMock(
        side_effect=RuntimeConnectionClosedError(
            message="connection closed",
            in_flight=(
                InflightRequestDisposition(
                    request_id="1",
                    method="runtime.initialize",
                    disposition="failed_connection_closed",
                ),
            ),
        )
    )

    mocker.patch(
        "kiln.sdk.runtime_client.RuntimeStdioConnection",
        return_value=mock_connection,
    )

    # Call RuntimeClient.start and expect RuntimeProcessExitedError
    with pytest.raises(RuntimeProcessExitedError) as exc_info:
        await RuntimeClient.start()

    # Verify the exception contains exit_status info
    error = exc_info.value
    assert error.exit_status is not None
    assert error.exit_status.returncode == 1
    assert error.exit_status.signal is None
    assert "boom" in error.exit_status.stderr_tail

    # Verify in_flight tracking
    assert len(error.in_flight) == 1
    assert error.in_flight[0].method == "runtime.initialize"
    assert error.in_flight[0].disposition == "failed_connection_closed"
