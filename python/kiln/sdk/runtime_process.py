import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import IO

from .errors import StdinUnavailableError, StdoutUnavailableError


@dataclass
class RuntimeProcess:
    process: subprocess.Popen[bytes]

    @property
    def stdin(self) -> IO[bytes]:
        if self.process.stdin is None:
            raise StdinUnavailableError
        return self.process.stdin

    @property
    def stdout(self) -> IO[bytes]:
        if self.process.stdout is None:
            raise StdoutUnavailableError
        return self.process.stdout

    @classmethod
    def start(cls, binary: Path | None = None) -> "RuntimeProcess":
        binary = binary or _find_runtime_binary()

        process = subprocess.Popen(
            [str(binary)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=None,
            env=_runtime_environment(),
        )

        return cls(process=process)

    def close(self) -> None:
        if self.process.poll() is not None:
            return

        self.process.terminate()

        try:
            self.process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self.process.kill()
            self.process.wait()


def _find_runtime_binary() -> Path:
    configured = os.environ.get("KILN_RUNTIME_BINARY")
    if configured:
        return Path(configured)

    return Path("dist/bin/kiln-runtime").resolve()


def _runtime_environment() -> dict[str, str]:
    allowed = ("PATH", "HOME", "USERPROFILE", "TMPDIR", "TEMP", "TMP")

    return {key: value for key in allowed if (value := os.environ.get(key)) is not None}
