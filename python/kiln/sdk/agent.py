from dataclasses import dataclass
from pathlib import Path

from kiln.models.budget import Budget
from kiln.models.run import RunResult

from .client import RuntimeClient
from .errors import RepositoryNotFoundError, TaskEmptyError
from .runtime_process import RuntimeProcess


@dataclass(frozen=True)
class AgentConfig:
    repository: Path
    budget: Budget


class Agent:
    def __init__(
        self,
        config: AgentConfig,
        process: RuntimeProcess,
        client: RuntimeClient,
    ) -> None:
        self._config = config
        self._process = process
        self._client = client

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
        client = RuntimeClient(process)

        return cls(
            config=AgentConfig(
                repository=repository_path,
                budget=budget,
            ),
            process=process,
            client=client,
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
