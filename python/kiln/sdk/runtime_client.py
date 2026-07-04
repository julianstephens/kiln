from pathlib import Path
from typing import NoReturn

from kiln.models.budget import Budget
from kiln.models.run import RunResult
from kiln.protocol.errors import RuntimeConnectionClosedError

from .errors import RuntimeProcessError, RuntimeProcessExitedError
from .runtime_connection import RuntimeConnectionState, RuntimeStdioConnection
from .runtime_process import RuntimeProcess


class RuntimeClient:
    """Represents a client that connects to a runtime process and allows interaction
    with it."""

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

        try:
            connection = RuntimeStdioConnection(
                process=process.process, state=RuntimeConnectionState.STARTING
            )
            await connection.initialize()
            health = await connection.health()
            if not health.root.ready:
                _raise_not_ready()

            return cls(process, connection)
        except RuntimeConnectionClosedError as exc:
            exit_status = process.exit_status
            if exit_status is not None and not exit_status.expected:
                raise RuntimeProcessExitedError(
                    exit_status=exit_status,
                    in_flight=exc.in_flight
                    or connection.inflight_disposition("failed_process_exited"),
                ) from exc
            raise
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
