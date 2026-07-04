from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class RuntimeExitStatus:
    expected: bool
    returncode: int
    signal: int
    stderr_tail: str


InflightDisposition = Literal[
    "completed",
    "failed_connection_closed",
    "failed_process_exited",
    "cancelled",
    "unknown",
]


@dataclass(frozen=True)
class InflightRequestDisposition:
    request_id: str
    method: str
    disposition: InflightDisposition


@dataclass(frozen=True)
class RuntimeConnectionFailure:
    in_flight: tuple[InflightRequestDisposition, ...]


class StderrTailBuffer:
    def __init__(self, max_bytes: int = 16_384):
        self._max_bytes = max_bytes
        self._buf = bytearray()

    def append(self, data: bytes) -> None:
        self._buf.extend(data)
        if len(self._buf) > self._max_bytes:
            del self._buf[: len(self._buf) - self._max_bytes]

    def text(self) -> str:
        return self._buf.decode("utf-8", errors="replace")
