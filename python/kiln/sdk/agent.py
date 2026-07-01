from dataclasses import dataclass
from pathlib import Path

from kiln.models.budget import Budget
from kiln.models.run import RunResult

from .client import RuntimeClient
from .errors import RepositoryNotFoundError, TaskEmptyError


@dataclass(frozen=True)
class AgentConfig:
    repository: Path
    budget: Budget


class Agent:
    _config: AgentConfig
    _client: RuntimeClient

    def __init__(
        self,
        config: AgentConfig,
        client: RuntimeClient,
    ) -> None:
        self._config = config
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

        client = await RuntimeClient.start()

        return cls(
            config=AgentConfig(
                repository=repository_path,
                budget=budget,
            ),
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
        await self._client.close()

    async def __aenter__(self) -> "Agent":
        return self

    async def __aexit__(self, *_: object) -> None:
        await self.close()
