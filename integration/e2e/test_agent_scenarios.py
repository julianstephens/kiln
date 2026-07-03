"""Parameterized e2e tests for Agent scenarios.

Each scenario is run independently. New tests are added by:
1. Creating a scenario class in scenarios/agent_lifecycle.py or similar
2. Exporting it from scenarios/__init__.py
3. Adding it to SCENARIOS list below

No test function boilerplate needed.
"""

from pathlib import Path

import pytest

from .scenarios import (
    AgentCloseScenario,
    EmptyTaskErrorScenario,
    InitializeAgentScenario,
    InvalidRepositoryErrorScenario,
    MultipleAgentLifecyclesScenario,
)

# All scenarios to test
SCENARIOS = [
    InitializeAgentScenario(),
    AgentCloseScenario(),
    MultipleAgentLifecyclesScenario(),
    InvalidRepositoryErrorScenario(),
    EmptyTaskErrorScenario(),
]


@pytest.mark.parametrize(
    "scenario",
    SCENARIOS,
    ids=lambda s: s.__class__.__name__,
)
@pytest.mark.anyio
async def test_agent_scenario(scenario, temp_repo: Path) -> None:
    """Run each scenario and verify it executes correctly.

    Args:
        scenario: Test scenario to execute
        temp_repo: Temporary repository for testing
    """
    await scenario.run(temp_repo)
