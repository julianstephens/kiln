from dataclasses import dataclass
from pathlib import Path

from kiln.models.budget import Budget
from kiln.models.run import RunResult
from kiln.schemas.runtime import RuntimeInitializeResult

from .client import RuntimeClient
from .errors import RepositoryNotFoundError, RuntimeProcessError, TaskEmptyError
from .runtime_connection import RuntimeStdioConnection
from .runtime_process import RuntimeProcess


@dataclass(frozen=True)
class AgentConfig:
    repository: Path
    budget: Budget


class Agent:
    _config: AgentConfig
    _process: RuntimeProcess
    _client: RuntimeClient
    _runtime: RuntimeInitializeResult

    def __init__(
        self,
        config: AgentConfig,
        process: RuntimeProcess,
        client: RuntimeClient,
        runtime: RuntimeInitializeResult,
    ) -> None:
        self._config = config
        self._process = process
        self._client = client
        self._runtime = runtime

    @classmethod
    async def open(
        cls,
        repository: str | Path,
        *,
        budget: Budget,
    ) -> "Agent":
        repository_path = Path(repository).resolve()

        if not repository_path.is_dir():
            raise RepositoryNotFoundError(str(repository_path))

        process = await RuntimeProcess.start()
        connection = RuntimeStdioConnection(process=process.process)
        initialize_result = await connection.initialize()
        health = await connection.health()
        if not health.root.ready:
            raise RuntimeProcessError(message=("runtime process is not ready"))
        client = RuntimeClient(process)

        return cls(
            config=AgentConfig(
                repository=repository_path,
                budget=budget,
            ),
            process=process,
            client=client,
            runtime=initialize_result,
        )

    def run(self, task: str) -> RunResult:
        if not task.strip():
            raise TaskEmptyError

        return self._client.create_run(
            repository=self._config.repository,
            task=task,
            budget=self._config.budget,
        )

    async def close(self) -> None:
        await self._process.aclose()

    async def __aenter__(self) -> "Agent":
        return self

    async def __aexit__(self, *_: object) -> None:
        await self.close()
