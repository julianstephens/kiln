from pathlib import Path

from kiln.models.budget import Budget
from kiln.models.run import RunResult

from .errors import RuntimeProcessError
from .runtime_connection import RuntimeStdioConnection
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
        connection = RuntimeStdioConnection(process=process.process)
        await connection.initialize()
        health = await connection.health()
        if not health.root.ready:
            raise RuntimeProcessError(message=("runtime process is not ready"))
        return cls(process, connection)

    def create_run(
        self,
        repository: Path,
        task: str,
        budget: Budget,
    ) -> RunResult:
        raise NotImplementedError("create_run is not yet implemented")

    async def close(self) -> None:
        """Close the connection to the runtime process."""
        await self._process.aclose()
