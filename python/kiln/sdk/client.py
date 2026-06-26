from pathlib import Path
from typing import BinaryIO

from kiln.models.budget import Budget
from kiln.models.run import RunResult

from .runtime_process import RuntimeProcess


class RuntimeClient:
    def __init__(self, process: RuntimeProcess):
        self._process = process

    @property
    def stdin(self) -> BinaryIO:
        return self._process.stdin  # type: ignore

    @property
    def stdout(self) -> BinaryIO:
        return self._process.stdout  # type: ignore

    @classmethod
    def start(cls, binary: Path | None = None) -> "RuntimeClient":
        process = RuntimeProcess.start(binary)
        return cls(process)

    def create_run(
        self,
        repository: Path,
        task: str,
        budget: Budget,
    ) -> RunResult:
        raise NotImplementedError("create_run is not yet implemented")
