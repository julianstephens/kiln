import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

import anyio

from ._runtime_os.posix import terminate_posix_process_tree
from ._runtime_os.win32 import (
    ServerProcess,
    create_windows_process,
    terminate_windows_process_tree,
)
from .errors import (
    MissingRuntimeBinaryError,
)


@dataclass
class RuntimeProcess:
    process: ServerProcess

    @property
    def is_alive(self) -> bool:
        return self.process.returncode is None

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
                stderr=sys.stderr,
                env=_runtime_environment(),
                start_new_session=True,
            )

        return cls(process=process)

    async def aclose(self) -> None:
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
