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
from .errors import MissingRuntimeBinaryError
from .runtime_exit import RuntimeExitStatus, StderrTailBuffer

if sys.platform == "win32":
    from ._runtime_os.win32 import normalize_exit_status
else:
    from ._runtime_os.posix import normalize_exit_status


@dataclass
class RuntimeProcess:
    process: ServerProcess
    _stderr_tail: StderrTailBuffer = field(default_factory=StderrTailBuffer)
    _expected_exit: bool = False
    _last_exit_status: RuntimeExitStatus | None = None

    @property
    def is_alive(self) -> bool:
        return self.process.returncode is None

    @property
    def exit_status(self) -> RuntimeExitStatus | None:
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

    @classmethod
    async def start(cls, binary: Path | None = None) -> "RuntimeProcess":
        binary = binary or _find_runtime_binary()

        if sys.platform == "win32":
            process = await create_windows_process(
                command=str(binary),
                args=[],
                errlog=sys.stderr,
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

    async def aclose(self) -> None:
        self._expected_exit = True
        if sys.platform == "win32":
            await terminate_windows_process_tree(self.process)
        else:
            await terminate_posix_process_tree(self.process)  # type: ignore


def _find_runtime_binary() -> Path:
    configured = os.environ.get("KILN_RUNTIME_BINARY")
    if configured:
        return Path(configured)

    raise MissingRuntimeBinaryError


def _runtime_environment() -> dict[str, str]:
    allowed = ("PATH", "HOME", "USERPROFILE", "TMPDIR", "TEMP", "TMP")

    return {key: value for key in allowed if (value := os.environ.get(key)) is not None}
