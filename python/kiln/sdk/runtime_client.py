from pathlib import Path
from typing import NoReturn

from kiln.models.budget import Budget
from kiln.models.run import RunResult

from .errors import RuntimeProcessError, RuntimeProcessExitedError
from .runtime_connection import RuntimeStdioConnection
from .runtime_exit import InflightRequestDisposition, RuntimeExitStatus
from .runtime_process import RuntimeProcess


class RuntimeClient:
    def __init__(
        self, process: RuntimeProcess, connection: RuntimeStdioConnection
    ) -> None:
        self._process = process
        self._connection = connection

    @classmethod
    async def start(cls, binary: Path | None = None) -> "RuntimeClient":
        """Start a new runtime process and establish a connection to it.

        Args:
            binary: Optional path to the runtime binary. If not provided, the default
                binary will be used.

        Returns:
            An instance of `RuntimeClient` representing the connection to the runtime
                process.

        Raises:
            RuntimeProcessError: If the runtime process fails to start or is not ready.
        """
        process = await RuntimeProcess.start(binary)

        def _raise_not_ready() -> NoReturn:
            raise RuntimeProcessError(message=("runtime process is not ready"))

        def _raise_unexpected_exit(
            exit_status: RuntimeExitStatus,
            in_flight: tuple[InflightRequestDisposition, ...],
        ) -> NoReturn:
            raise RuntimeProcessExitedError(
                exit_status=exit_status, in_flight=in_flight
            )

        try:
            connection = RuntimeStdioConnection(process=process.process)
            await connection.initialize()
            if process.exit_status is not None:
                _raise_unexpected_exit(
                    process.exit_status,
                    connection.inflight_disposition("failed_process_exited"),
                )

            health = await connection.health()
            if not health.root.ready:
                _raise_not_ready()

            return cls(process, connection)
        except BaseException:
            await process.aclose()
            raise

    async def create_run(
        self,
        repository: Path,
        task: str,
        budget: Budget,
    ) -> RunResult:
        raise NotImplementedError("create_run is not yet implemented")

    async def close(self) -> None:
        """Close the connection to the runtime process."""
        await self._process.aclose()
