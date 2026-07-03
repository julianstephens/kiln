"""Pytest configuration for integration tests.

Manages Go runtime subprocess lifecycle and provides fixtures for e2e tests.
"""

import os
import subprocess
import sys
from pathlib import Path

import pytest


def _get_runtime_binary() -> Path:
    """Get path to kiln-runtime binary, building if needed."""
    workspace_root = Path(__file__).parent.parent
    binary_path = workspace_root / "dist" / "bin" / "kiln-runtime"

    # If binary doesn't exist, build it
    if not binary_path.exists():
        print(f"\nBuilding Go runtime to {binary_path}...", file=sys.stderr)
        result = subprocess.run(
            ["make", "build-go"],
            cwd=workspace_root,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise RuntimeError(
                f"Failed to build Go runtime:\nstdout: {result.stdout}\nstderr: {result.stderr}"
            )

    return binary_path


@pytest.fixture(scope="session", autouse=True)
def _set_runtime_binary_env() -> None:
    """Set KILN_RUNTIME_BINARY environment variable for all tests.

    This runs automatically before any tests execute, making the binary
    path available to Agent.open() without needing to pass it explicitly.
    """
    binary = _get_runtime_binary()
    os.environ["KILN_RUNTIME_BINARY"] = str(binary)


@pytest.fixture
def temp_repo(tmp_path: Path) -> Path:
    """Create a minimal test repository."""
    repo = tmp_path / "test-repo"
    repo.mkdir(parents=True)

    # Create minimal .git directory structure for testing
    git_dir = repo / ".git"
    git_dir.mkdir(parents=True)
    (git_dir / "HEAD").write_text("ref: refs/heads/main\n")
    (git_dir / "refs" / "heads").mkdir(parents=True)
    (git_dir / "objects").mkdir(parents=True)

    return repo
