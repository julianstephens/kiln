"""Integration tests for RuntimeClient startup and lifecycle."""

from __future__ import annotations

from contextlib import nullcontext
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, PropertyMock, call

import anyio
import pytest
from pytest_mock import MockerFixture

from kiln.protocol.errors import RuntimeConnectionClosedError
from kiln.protocol.pending import InflightRequestDisposition
from kiln.sdk.config import ShutdownConfig
from kiln.sdk.errors import RuntimeProcessExitedError
from kiln.sdk.runtime_client import RuntimeClient
from kiln.sdk.runtime_connection import RuntimeConnectionState, RuntimeStdioConnection
from kiln.sdk.runtime_exit import (
    RuntimeExitStatus,
    RuntimeFinalExitClass,
    StderrTailBuffer,
)


def _mock_process_lifecycle(
    process: MagicMock,
    *,
    wait_side_effect: list[object | BaseException] | None = None,
) -> None:
    """Configure a process mock to look alive until wait/terminate completes."""
    type(process).is_alive = PropertyMock(side_effect=[True, False])
    process.wait = AsyncMock(side_effect=wait_side_effect or [None])


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
        timeout=False,
        returncode=1,
        signal=None,
        stderr_tail="boom",
        final_class=RuntimeFinalExitClass.STARTUP_FAILURE,
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
    assert error.exit_status.final_class == RuntimeFinalExitClass.STARTUP_FAILURE

    # Verify in_flight tracking
    assert len(error.in_flight) == 1
    assert error.in_flight[0].method == "runtime.initialize"
    assert error.in_flight[0].disposition == "failed_connection_closed"


@pytest.mark.anyio
async def test_close_uses_configured_process_exit_timeout(mocker) -> None:
    """Test that close() uses process_exit_timeout_seconds from ShutdownConfig.

    Verifies:
    - The timeout is passed from ShutdownConfig to the polling operation
    """
    from kiln.sdk.runtime_connection import ShutdownConfig

    # Create fake process and connection mocks
    fake_runtime_process = MagicMock()
    fake_runtime_process.write_closed = False
    fake_runtime_process.close_stdin = AsyncMock()
    fake_runtime_process.aclose = AsyncMock()
    _mock_process_lifecycle(fake_runtime_process)
    fake_runtime_process.exit_status = RuntimeExitStatus(
        expected=True,
        timeout=False,
        returncode=0,
        signal=None,
        stderr_tail="",
        final_class=RuntimeFinalExitClass.GRACEFUL_EXIT,
    )

    # Create mock connection with configured timeout
    mock_connection = MagicMock(spec=RuntimeStdioConnection)
    mock_connection.state = RuntimeConnectionState.READY
    mock_connection.shutdown_config = ShutdownConfig(
        kill_timeout_seconds=3,
        process_exit_timeout_seconds=5,  # Custom timeout for test
        cancel_in_flight_requests=True,
    )
    mock_connection.shutdown = AsyncMock(
        return_value=MagicMock(
            root=MagicMock(accepted=True, draining=True, shutdown=False)
        )
    )
    mock_connection.drain_stderr = AsyncMock()

    mocker.patch(
        "kiln.sdk.runtime_client.RuntimeStdioConnection",
        return_value=mock_connection,
    )
    mocker.patch(
        "kiln.sdk.runtime_client.RuntimeProcess.start",
        new_callable=AsyncMock,
        return_value=fake_runtime_process,
    )
    fail_after = mocker.patch(
        "kiln.sdk.runtime_client.anyio.fail_after",
        return_value=nullcontext(),
    )

    client = RuntimeClient(fake_runtime_process, mock_connection)

    # Call close
    await client.close()

    # Verify the configured timeout is used
    fail_after.assert_called_once_with(5)
    fake_runtime_process.close_stdin.assert_awaited_once()
    fake_runtime_process.wait.assert_awaited_once()
    fake_runtime_process.aclose.assert_not_awaited()
    assert client.runtime_exit_status is not None
    assert client.runtime_exit_status.final_class == RuntimeFinalExitClass.GRACEFUL_EXIT
    assert client.runtime_exit_status.timeout is False
    assert mock_connection.state == RuntimeConnectionState.EXITED


@pytest.mark.anyio
async def test_close_uses_default_process_exit_timeout_when_not_configured(
    mocker,
) -> None:
    """Test that close() uses default process_exit_timeout_seconds if not
    explicitly set.

    Verifies:
    - DefaultShutdownConfig has a sensible default timeout
    - The default is used when ShutdownConfig is created without explicit timeout
    """

    # Verify default timeout is set
    assert ShutdownConfig().process_exit_timeout_seconds == 30

    # Create fake process and connection mocks
    fake_runtime_process = MagicMock()
    fake_runtime_process.write_closed = False
    fake_runtime_process.close_stdin = AsyncMock()
    fake_runtime_process.aclose = AsyncMock()
    _mock_process_lifecycle(fake_runtime_process)
    fake_runtime_process.exit_status = RuntimeExitStatus(
        expected=True,
        timeout=False,
        returncode=0,
        signal=None,
        stderr_tail="",
        final_class=RuntimeFinalExitClass.GRACEFUL_EXIT,
    )

    # Create mock connection with default timeout
    mock_connection = MagicMock(spec=RuntimeStdioConnection)
    mock_connection.state = RuntimeConnectionState.READY
    mock_connection.shutdown_config = ShutdownConfig()
    mock_connection.shutdown = AsyncMock(
        return_value=MagicMock(
            root=MagicMock(accepted=True, draining=True, shutdown=False)
        )
    )
    mock_connection.drain_stderr = AsyncMock()

    mocker.patch(
        "kiln.sdk.runtime_client.RuntimeStdioConnection",
        return_value=mock_connection,
    )
    mocker.patch(
        "kiln.sdk.runtime_client.RuntimeProcess.start",
        new_callable=AsyncMock,
        return_value=fake_runtime_process,
    )
    fail_after = mocker.patch(
        "kiln.sdk.runtime_client.anyio.fail_after",
        return_value=nullcontext(),
    )

    # Create client
    client = RuntimeClient(fake_runtime_process, mock_connection)

    # Call close
    await client.close()

    # Verify the default timeout is used
    fail_after.assert_called_once_with(30)
    fake_runtime_process.close_stdin.assert_awaited_once()
    fake_runtime_process.wait.assert_awaited_once()
    fake_runtime_process.aclose.assert_not_awaited()
    assert client.runtime_exit_status is not None
    assert client.runtime_exit_status.final_class == RuntimeFinalExitClass.GRACEFUL_EXIT
    assert client.runtime_exit_status.timeout is False
    assert mock_connection.state == RuntimeConnectionState.EXITED


@pytest.mark.anyio
async def test_close_fallback_to_terminate(
    mocker: MockerFixture,
) -> None:
    """Test that close() manually terminates the process tree if the proccess does not
    close in `process_exit_timeout_seconds`.

    Verifies:
    """

    # Verify default timeout is set
    assert ShutdownConfig().process_exit_timeout_seconds == 30

    # Create fake process and connection mocks
    fake_runtime_process = MagicMock()
    fake_runtime_process.write_closed = False
    fake_runtime_process.close_stdin = AsyncMock()
    fake_runtime_process.aclose = AsyncMock()
    _mock_process_lifecycle(fake_runtime_process, wait_side_effect=[TimeoutError, None])
    fake_runtime_process.exit_status = RuntimeExitStatus(
        expected=True,
        timeout=True,
        returncode=0,
        signal=None,
        stderr_tail="",
        final_class=RuntimeFinalExitClass.FORCED_KILL,
    )

    # Create mock connection with default timeout
    mock_connection = MagicMock(spec=RuntimeStdioConnection)
    mock_connection.state = RuntimeConnectionState.READY
    mock_connection.shutdown_config = ShutdownConfig()
    mock_connection.shutdown = AsyncMock(
        return_value=MagicMock(
            root=MagicMock(accepted=True, draining=True, shutdown=False)
        )
    )
    mock_connection.drain_stderr = AsyncMock()

    mocker.patch(
        "kiln.sdk.runtime_client.RuntimeStdioConnection",
        return_value=mock_connection,
    )
    mocker.patch(
        "kiln.sdk.runtime_client.RuntimeProcess.start",
        new_callable=AsyncMock,
        return_value=fake_runtime_process,
    )
    fail_after = mocker.patch(
        "kiln.sdk.runtime_client.anyio.fail_after",
        return_value=nullcontext(),
    )

    # Create client
    client = RuntimeClient(fake_runtime_process, mock_connection)

    # Call close
    await client.close()

    # Verify the default timeout is used
    assert fail_after.call_args_list == [call(30), call(10)]
    fake_runtime_process.close_stdin.assert_awaited_once()
    assert fake_runtime_process.wait.await_count == 2
    fake_runtime_process.aclose.assert_awaited_once_with(
        mark_expected=True, final_class=RuntimeFinalExitClass.FORCED_KILL, timeout=True
    )
    assert client.runtime_exit_status is not None
    assert client.runtime_exit_status.final_class == RuntimeFinalExitClass.FORCED_KILL
    assert client.runtime_exit_status.timeout is True
    assert mock_connection.state == RuntimeConnectionState.EXITED


@pytest.mark.anyio
async def test_close_terminates_live_process_after_startup_failure() -> None:
    process = MagicMock()
    process.aclose = AsyncMock()
    process.wait = AsyncMock()
    process.exit_status = MagicMock()
    type(process).is_alive = PropertyMock(side_effect=[True, False])

    connection = MagicMock(spec=RuntimeStdioConnection)
    connection.state = RuntimeConnectionState.FAILED
    connection.shutdown_config = ShutdownConfig()

    client = RuntimeClient(process, connection)
    client._task_group = MagicMock()
    client._exit_stack = AsyncMock()

    with anyio.fail_after(1):
        await client.close(mark_expected=False)

    process.aclose.assert_awaited_once_with(
        mark_expected=False,
        final_class=RuntimeFinalExitClass.STARTUP_FAILURE,
    )
    process.wait.assert_awaited_once()
    client._task_group.cancel_scope.cancel.assert_called_once()
    client._exit_stack.aclose.assert_awaited_once()
