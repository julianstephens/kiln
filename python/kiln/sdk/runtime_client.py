from contextlib import AsyncExitStack
from pathlib import Path
from typing import NoReturn

import anyio
from anyio.abc import TaskGroup

from kiln.models.budget import Budget
from kiln.models.run import RunResult
from kiln.protocol.errors import RuntimeConnectionClosedError

from .errors import RuntimeProcessError, RuntimeProcessExitedError
from .runtime_connection import (
    DefaultShutdownConfig,
    RuntimeConnectionState,
    RuntimeStdioConnection,
    ShutdownConfig,
)
from .runtime_process import RuntimeProcess


class RuntimeClient:
    """Represents a client that connects to a runtime process and allows interaction
    with it."""

    _process: RuntimeProcess
    _connection: RuntimeStdioConnection

    _exit_stack: AsyncExitStack | None
    _task_group: TaskGroup | None
    _runtime_exit_status: int
    _closed: bool

    def __init__(
        self,
        process: RuntimeProcess,
        connection: RuntimeStdioConnection,
    ) -> None:
        self._process = process
        self._connection = connection
        self._exit_stack = None
        self._task_group = None
        self._closed = False

    async def _open_bg_tasks(self) -> None:
        stack = AsyncExitStack()
        tg = await stack.enter_async_context(anyio.create_task_group())
        tg.start_soon(self._connection.drain_stderr)
        self._exit_stack = stack
        self._task_group = tg

    @classmethod
    async def start(
        cls,
        binary: Path | None = None,
        shutdown: ShutdownConfig = DefaultShutdownConfig,
    ) -> "RuntimeClient":
        """Start a new runtime process and establish a connection to it.

        Args:
            binary: Optional path to the runtime binary. If not provided, the default
                binary will be used.
            shutdown: The shutdown configuration that defines how the runtime process
                should be shut down. Defaults to DefaultShutdownConfig.

        Returns:
            An instance of `RuntimeClient` representing the connection to the runtime
                process.

        Raises:
            RuntimeProcessError: If the runtime process fails to start or is not ready.
        """
        process = await RuntimeProcess.start(binary)
        connection = RuntimeStdioConnection(
            process=process.process,
            state=RuntimeConnectionState.STARTING,
            stderr_tail=process.stderr_tail,
            shutdown_config=shutdown,
        )
        client = cls(process, connection)

        def _raise_not_ready() -> NoReturn:
            raise RuntimeProcessError(message=("runtime process is not ready"))

        try:
            await client._open_bg_tasks()

            await connection.initialize()
            health = await connection.health()
            if not health.root.ready:
                _raise_not_ready()
        except RuntimeConnectionClosedError as exc:
            connection.mark_failed()

            exit_status = process.exit_status
            if exit_status is not None and not exit_status.expected:
                await client.close(mark_expected=False)
                raise RuntimeProcessExitedError(
                    exit_status=exit_status,
                    in_flight=exc.in_flight
                    or connection.inflight_disposition("failed_process_exited"),
                ) from exc
            await client.close(mark_expected=False)
            raise
        except BaseException:
            connection.mark_failed()
            await client.close(mark_expected=False)
            raise
        else:
            return client

    async def create_run(
        self,
        repository: Path,
        task: str,
        budget: Budget,
    ) -> RunResult:
        raise NotImplementedError("create_run is not yet implemented")

    async def close(self, mark_expected: bool = True) -> None:
        """Close the connection to the runtime process."""
        if self._closed:
            return
        self._closed = True

        try:
            if (
                not self._process.is_alive
                or self._connection.state == RuntimeConnectionState.FAILED
            ):
                return
            res = await self._connection.shutdown()
            if not res.root.accepted and not (res.root.draining or res.root.shutdown):
                raise RuntimeProcessError(
                    message="runtime process refused to shutdown gracefully"
                )
            await self._process.aclose(mark_expected=mark_expected)
        finally:
            if self._exit_stack is not None:
                await self._exit_stack.aclose()
            if self._connection.state != RuntimeConnectionState.FAILED:
                self._connection.state = RuntimeConnectionState.EXITED
