from dataclasses import dataclass
from pathlib import Path

from structlog import BoundLogger, get_logger

from kiln.logger import DefaultLoggingConfig, LoggingConfig, configure_logging
from kiln.models.budget import Budget
from kiln.models.run import RunResult

from .errors import RepositoryNotFoundError, TaskEmptyError
from .runtime_client import RuntimeClient
from .runtime_connection import DefaultShutdownConfig, ShutdownConfig


@dataclass(frozen=True)
class AgentConfig:
    """Represents the configuration for an Agent instance."""

    # The path to the source control repository that the agent will interact with.
    repository: Path
    # The budget configuration that defines the resource limits for the agent's
    # operations.
    budget: Budget
    # The logging configuration that defines how the agent will log its operations.
    logging: LoggingConfig
    # The shutdown configuration that defines how the agent will shutdown the
    # Go runtime.
    shutdown: ShutdownConfig


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
        configure_logging(config.logging)
        self._logger = get_logger(__name__).bind(repository=str(config.repository))

    @classmethod
    async def open(
        cls,
        repository: str | Path,
        *,
        budget: Budget,
        logging: LoggingConfig = DefaultLoggingConfig,
        shutdown: ShutdownConfig = DefaultShutdownConfig,
    ) -> "Agent":
        """Open an agent for the given repository with the specified budget and logging
        configuration. Agent instance is created and initialized asynchronously,
        establishing a connection to the runtime client.

        Args:
            repository: The path to the source control repository that the agent will
                interact with. Can be a string or a Path object.
            budget: The budget configuration that defines the resource limits for the
                agent's operations.
            logging: The logging configuration that defines how the agent will log its
                operations. Defaults to stderr config
            shutdown: The shutdown configuration that defines how the agent will
                shutdown the Go runtime. Defaults to DefaultShutdownConfig.

        """
        repository_path = Path(repository).resolve()

        if not repository_path.is_dir():
            raise RepositoryNotFoundError(str(repository_path))

        client = await RuntimeClient.start(shutdown=shutdown)

        return cls(
            config=AgentConfig(
                repository=repository_path,
                budget=budget,
                logging=logging,
                shutdown=shutdown,
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
