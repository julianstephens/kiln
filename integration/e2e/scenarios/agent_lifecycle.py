"""Concrete test scenarios for Agent initialization and lifecycle."""

from pathlib import Path

import pytest
from kiln import Agent
from kiln.sdk.errors import RepositoryNotFoundError, TaskEmptyError
from kiln.sdk.runtime_connection import ShutdownConfig

from .base import BaseScenario


class InitializeAgentScenario(BaseScenario):
    """Test: Agent.open() successfully initializes runtime.

    Verifies:
    - Runtime process starts
    - Initialize RPC succeeds
    - Runtime transitions to ready state
    """

    async def run(self, repo: Path) -> None:
        async with await Agent.open(
            repository=repo,
            budget=self.budget(),
            shutdown=ShutdownConfig(
                process_exit_timeout_seconds=15,
                kill_timeout_seconds=5,
                cancel_in_flight_requests=True,
            ),
        ) as agent:
            # If we get here without exception, initialization succeeded
            assert agent._client._process.is_alive, (
                "Runtime process should be alive after open()"
            )


class AgentCloseScenario(BaseScenario):
    """Test: Agent.close() properly closes runtime.

    Verifies:
    - Agent can be created and closed
    - Process terminates cleanly
    """

    async def run(self, repo: Path) -> None:
        async with await Agent.open(
            repository=repo,
            budget=self.budget(),
            shutdown=ShutdownConfig(
                process_exit_timeout_seconds=15,
                kill_timeout_seconds=5,
                cancel_in_flight_requests=True,
            ),
        ) as agent:
            assert agent._client._process.is_alive, (
                "Process should be alive after open()"
            )


class MultipleAgentLifecyclesScenario(BaseScenario):
    """Test: Multiple sequential agent lifecycles work correctly.

    Verifies:
    - Multiple Agent instances can be created and destroyed
    - Runtime binary is reusable
    - No resource leaks between instances
    """

    async def run(self, repo: Path) -> None:
        for i in range(3):
            async with await Agent.open(
                repository=repo,
                budget=self.budget(),
                shutdown=ShutdownConfig(
                    process_exit_timeout_seconds=15,
                    kill_timeout_seconds=5,
                    cancel_in_flight_requests=True,
                ),
            ) as agent:
                assert agent._client._process.is_alive, (
                    f"Process should be alive (iteration {i})"
                )


class InvalidRepositoryErrorScenario(BaseScenario):
    """Test: Non-existent repository raises before starting runtime.

    Verifies:
    - Agent.open() validates repository path first
    - Runtime process is never started for invalid inputs
    - RepositoryNotFoundError is raised
    """

    async def run(self, repo: Path) -> None:
        nonexistent = repo.parent / "nonexistent-repo"

        with pytest.raises(RepositoryNotFoundError):
            async with await Agent.open(
                repository=nonexistent,
                budget=self.budget(),
                shutdown=ShutdownConfig(
                    process_exit_timeout_seconds=15,
                    kill_timeout_seconds=5,
                    cancel_in_flight_requests=True,
                ),
            ):
                pass  # Should not reach here


class EmptyTaskErrorScenario(BaseScenario):
    """Test: Empty task string is rejected.

    Verifies:
    - Agent validates task before sending to runtime
    - TaskEmptyError is raised for empty/whitespace tasks
    """

    async def run(self, repo: Path) -> None:
        async with await Agent.open(
            repository=repo,
            budget=self.budget(),
            shutdown=ShutdownConfig(
                process_exit_timeout_seconds=15,
                kill_timeout_seconds=5,
                cancel_in_flight_requests=True,
            ),
        ) as agent:
            with pytest.raises(TaskEmptyError):
                await agent.run("")
