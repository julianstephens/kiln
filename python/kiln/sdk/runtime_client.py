from contextlib import AsyncExitStack
from pathlib import Path
from typing import NoReturn

import anyio
from anyio.abc import TaskGroup

from kiln.models.budget import Budget
from kiln.models.run import RunResult
from kiln.protocol.errors import RuntimeConnectionClosedError
from kiln.schemas.runtime.error import KilnError

from .config import RuntimeConfig, ShutdownConfig
from .errors import (
    RuntimeMethodError,
    RuntimeProcessError,
    RuntimeProcessExitedError,
    RuntimeStartupError,
)
from .runtime_connection import (
    RuntimeConnectionState,
    RuntimeStdioConnection,
)
from .runtime_exit import RuntimeExitStatus, RuntimeFinalExitClass
from .runtime_process import RuntimeProcess


class RuntimeClient:
    """Represents a client that connects to a runtime process and allows interaction
    with it."""

    _process: RuntimeProcess
    _connection: RuntimeStdioConnection

    _exit_stack: AsyncExitStack | None
    _task_group: TaskGroup | None
    _runtime_exit_status: RuntimeExitStatus | None = None
    _closed: bool

    def __init__(
        self,
        process: RuntimeProcess,
        connection: RuntimeStdioConnection,
    ) -> None:
        self._process = process
        self._connection = connection
        self._exit_stack = None
        self._runtime_exit_status = None
        self._task_group = None
        self._closed = False

    async def _open_bg_tasks(self) -> None:
        stack = AsyncExitStack()
        tg = await stack.enter_async_context(anyio.create_task_group())
        tg.start_soon(self._connection.drain_stderr)
        self._exit_stack = stack
        self._task_group = tg

    @property
    def runtime_exit_status(self) -> RuntimeExitStatus | None:
        """The exit status of the runtime process, or None if it is still running."""
        return self._runtime_exit_status

    @classmethod
    async def start(
        cls,
        binary: Path | None = None,
        shutdown: ShutdownConfig | None = None,
        config: RuntimeConfig | None = None,
    ) -> "RuntimeClient":
        """Start a new runtime process and establish a connection to it.

        Args:
            binary: Optional path to the runtime binary. If not provided, the default
                binary will be used.
            config: Optional configuration for the runtime client. If not provided, the
                default configuration will be used.

        Returns:
            An instance of `RuntimeClient` representing the connection to the runtime
                process.

        Raises:
            RuntimeProcessError: If the runtime process fails to start or is not ready.
            RuntimeProcessExitedError: If the runtime process exits unexpectedly during
                startup.
            RuntimeMethodError: If there is an error during the initialization of the
                connection.
            RuntimeConnectionClosedError: If the connection to the runtime process is
                closed unexpectedly during startup.
        """
        if shutdown is None:
            shutdown = ShutdownConfig()
        if config is None:
            config = RuntimeConfig()

        process = await RuntimeProcess.start(binary=binary, config=config)
        connection = RuntimeStdioConnection(
            process=process.process,
            state=RuntimeConnectionState.STARTING,
            stderr_tail=process.stderr_tail,
            shutdown_config=shutdown,
        )
        client = cls(process, connection)

        def _raise_startup_failure(fatal: KilnError) -> NoReturn:
            raise RuntimeStartupError(fatal)

        def _raise_not_ready() -> NoReturn:
            raise RuntimeProcessError(message=("runtime initialized but is not ready"))

        try:
            await client._open_bg_tasks()

            await connection.initialize()
            health = await connection.health()
            if not health.root.ready:
                if fatal := health.root.last_fatal_startup_error:
                    _raise_startup_failure(fatal)  # type: ignore
                _raise_not_ready()
        except RuntimeConnectionClosedError as exc:
            connection.mark_failed()

            if process.exit_status is not None:
                process.mark_final_exit_class(RuntimeFinalExitClass.STARTUP_FAILURE)
                exit_status = process.exit_status
                await client.close(mark_expected=False)
                raise RuntimeProcessExitedError(
                    exit_status=exit_status,
                    in_flight=exc.in_flight
                    or connection.inflight_disposition("failed_process_exited"),
                ) from exc
            await client.close(mark_expected=False)
            raise
        except RuntimeMethodError:
            connection.mark_failed()
            process.mark_final_exit_class(RuntimeFinalExitClass.INITIALIZE_FAILURE)
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
            if self._process.is_alive:
                if self._connection.state != RuntimeConnectionState.FAILED:
                    await self._try_graceful_shutdown(mark_expected=mark_expected)
                else:
                    await self._terminate_failed_process(mark_expected=mark_expected)

            if self._process.is_alive:
                await self._force_terminate(mark_expected=mark_expected)

            self._runtime_exit_status = self._process.exit_status
        finally:
            if self._task_group is not None:
                self._task_group.cancel_scope.cancel()

            if self._exit_stack is not None:
                await self._exit_stack.aclose()

            if self._connection.state != RuntimeConnectionState.FAILED:
                self._connection.state = RuntimeConnectionState.EXITED

    async def _try_graceful_shutdown(self, *, mark_expected: bool) -> None:
        try:
            res = await self._connection.shutdown()

            if not res.root.accepted and not (res.root.draining or res.root.shutdown):
                raise RuntimeProcessError(
                    message="runtime process refused to shutdown gracefully"
                )

            if not self._process.write_closed:
                await self._process.close_stdin()

            with anyio.fail_after(
                self._connection.shutdown_config.process_exit_timeout_seconds
            ):
                await self._process.wait()

            self._process.mark_final_exit_class(RuntimeFinalExitClass.GRACEFUL_EXIT)
        except (RuntimeConnectionClosedError, RuntimeMethodError, TimeoutError):
            await self._force_terminate(mark_expected=mark_expected)

    async def _force_terminate(self, *, mark_expected: bool) -> None:
        await self._process.aclose(
            mark_expected=mark_expected,
            final_class=RuntimeFinalExitClass.FORCED_KILL,
            timeout=True,
        )

        with anyio.fail_after(self._connection.shutdown_config.kill_timeout_seconds):
            await self._process.wait()

    async def _terminate_failed_process(self, *, mark_expected: bool) -> None:
        await self._process.aclose(
            mark_expected=mark_expected,
            final_class=RuntimeFinalExitClass.STARTUP_FAILURE,
        )

        with anyio.fail_after(self._connection.shutdown_config.kill_timeout_seconds):
            await self._process.wait()
