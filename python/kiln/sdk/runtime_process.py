import os
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

import anyio

from ._runtime_os.posix import terminate_posix_process_tree
from ._runtime_os.win32 import (
    ServerProcess,
    create_windows_process,
    terminate_windows_process_tree,
)
from .errors import MissingRuntimeBinaryError, RuntimeProcessError
from .runtime_exit import RuntimeExitStatus, StderrTailBuffer

if sys.platform == "win32":
    from ._runtime_os.win32 import normalize_exit_status
else:
    from ._runtime_os.posix import normalize_exit_status


@dataclass
class RuntimeProcess:
    """Represents a runtime process that can be started and monitored."""

    process: ServerProcess
    _write_closed: bool = False
    _stderr_tail: StderrTailBuffer = field(default_factory=StderrTailBuffer)
    _expected_exit: bool = False
    _last_exit_status: RuntimeExitStatus | None = None

    @property
    def is_alive(self) -> bool:
        """Whether the runtime process is still alive (i.e., has not exited)."""
        return self.process.returncode is None

    @property
    def write_closed(self) -> bool:
        """Whether the standard input of the runtime process has been closed."""
        return self._write_closed

    @property
    def exit_status(self) -> RuntimeExitStatus | None:
        """The exit status of the runtime process, or None if it is still running."""
        if self.process.returncode is None:
            return None

        exit_code, signal = normalize_exit_status(self.process.returncode)

        status = RuntimeExitStatus(
            expected=self._expected_exit,
            returncode=exit_code,
            signal=signal,
            stderr_tail=self._stderr_tail.text(),
        )
        self._last_exit_status = status
        return status

    @property
    def stderr_tail(self) -> StderrTailBuffer:
        """The tail of the runtime process's standard error output."""
        return self._stderr_tail

    @classmethod
    async def start(cls, binary: Path | None = None) -> "RuntimeProcess":
        """Start a new runtime process.

        Args:
            binary: Optional path to the runtime binary. If not provided, the default
                binary will be used.

        Returns:
            The `RuntimeProcess` instance representing the started process.
        """
        binary = binary or _find_runtime_binary()

        if sys.platform == "win32":
            process = await create_windows_process(
                command=str(binary),
                args=[],
                env=_runtime_environment(),
            )
        else:
            process = await anyio.open_process(
                command=[str(binary)],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=_runtime_environment(),
                start_new_session=True,
            )

        return cls(process=process)

    async def close_stdin(self) -> None:
        """Close the standard input of the runtime process, signaling that no more input
        will be sent."""
        if self.process.stdin is not None:
            await self.process.stdin.aclose()
            self._write_closed = True

    async def aclose(self, mark_expected: bool = True) -> None:
        """Close the runtime process, terminating it if it is still running."""
        if mark_expected and self.process.returncode is None:
            self._expected_exit = True
        await self.terminate_tree()

    async def terminate_tree(self) -> None:
        """Terminate the runtime process and its child processes."""
        if sys.platform == "win32":
            await terminate_windows_process_tree(self.process)
        else:
            await terminate_posix_process_tree(self.process)  # type: ignore

    async def wait(self) -> RuntimeExitStatus:
        """Wait for the runtime process to exit and return its exit status."""
        await self.process.wait()
        exit_status = self.exit_status
        if exit_status is None:
            raise RuntimeProcessError(message="process exited but exit status is None")
        return exit_status


def _find_runtime_binary() -> Path:
    configured = os.environ.get("KILN_RUNTIME_BINARY")
    if configured:
        return Path(configured)

    raise MissingRuntimeBinaryError


def _runtime_environment() -> dict[str, str]:
    allowed = ("PATH", "HOME", "USERPROFILE", "TMPDIR", "TEMP", "TMP")

    return {key: value for key in allowed if (value := os.environ.get(key)) is not None}
