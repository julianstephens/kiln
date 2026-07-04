"""Base scenario class for e2e tests.

Scenarios define sequences of agent operations without test boilerplate.
Each scenario extends BaseScenario and implements run() to specify test behavior.
"""

from abc import ABC, abstractmethod
from pathlib import Path

from kiln import Budget


class BaseScenario(ABC):
    """Test scenario defines a sequence of agent operations.

    Override run() to implement test behavior.
    Override budget() to customize runtime parameters.
    """

    def budget(self) -> Budget:
        """Return Budget configuration for this scenario.

        Override to customize for specific test needs.
        """
        return Budget(
            max_input_tokens=1_000,
            max_output_tokens=1_000,
            max_model_calls=1,
            max_repository_queries=5,
            max_turns=1,
        )

    @abstractmethod
    async def run(self, repo: Path) -> None:
        """Execute the scenario.

        Args:
            repo: Path to temporary test repository

        Raises:
            AssertionError if verification fails
            Any exception raised during execution
        """
        pass
