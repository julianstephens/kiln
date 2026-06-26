from dataclasses import dataclass
from typing import Literal

RunStatus = Literal["completed", "failed", "cancelled", "exhausted"]


@dataclass(frozen=True)
class RunResult:
    run_id: str
    status: RunStatus
    stop_reason: str
    answer: str | None
