from dataclasses import dataclass
from pathlib import Path

from structlog import BoundLogger, get_logger

from kiln.logger import configure_logging
from kiln.models.budget import Budget
from kiln.models.run import RunResult

from .config import RuntimeConfig, ShutdownConfig
from .errors import RepositoryNotFoundError, TaskEmptyError
from .runtime_client import RuntimeClient


@dataclass(frozen=True)
class AgentConfig:
    """Represents the configuration for an Agent instance."""

    # The path to the source control repository that the agent will interact with.
    repository: Path
    # The budget configuration that defines the resource limits for the agent's
    # operations.
    budget: Budget
    # The Runtime configuration that defines how the agent will be initialized and how
    # it will interact with the Go runtime.
    runtime: RuntimeConfig


class Agent:
    """An agent that interacts with a source control repository and manages tasks."""

    _config: AgentConfig
    _client: RuntimeClient
    _logger: BoundLogger

    def __init__(
        self,
        config: AgentConfig,
        client: RuntimeClient,
    ) -> None:
        """Initialize an Agent instance with the given configuration and runtime client.

        Agent instances are typically created using the `Agent.open` class method, which
        handles the asynchronous initialization of the runtime client.
        """
        self._config = config
        self._client = client
        configure_logging(config.runtime.logging)
        self._logger = get_logger(__name__).bind(repository=str(config.repository))

    @classmethod
    async def open(
        cls,
        repository: str | Path,
        *,
        binary: Path | None = None,
        budget: Budget,
        shutdown: ShutdownConfig | None = None,
        config: RuntimeConfig | None = None,
    ) -> "Agent":
        """Open an agent for the given repository with the specified budget and logging
        configuration. Agent instance is created and initialized asynchronously,
        establishing a connection to the runtime client.

        Args:
            repository: The path to the source control repository that the agent will
                interact with. Can be a string or a Path object.
            binary: Optional path to the runtime binary to be used by the agent. If not
                provided, the default binary will be used.
            budget: The budget configuration that defines the resource limits for the
                agent's operations.
            config: Optional runtime configuration that defines how the agent will be
                initialized and how it will interact with the Go runtime. If not
                provided, a default configuration will be used.

        """
        repository_path = Path(repository).resolve()

        if not repository_path.is_dir():
            raise RepositoryNotFoundError(str(repository_path))

        client = await RuntimeClient.start(
            config=config, shutdown=shutdown or ShutdownConfig(), binary=binary
        )

        return cls(
            config=AgentConfig(
                repository=repository_path,
                budget=budget,
                runtime=config or RuntimeConfig(),
            ),
            client=client,
        )

    async def run(self, task: str) -> RunResult:
        if not task.strip():
            raise TaskEmptyError

        return await self._client.create_run(
            repository=self._config.repository,
            task=task,
            budget=self._config.budget,
        )

    async def close(self) -> None:
        await self._client.close()

    async def __aenter__(self) -> "Agent":
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.close()
