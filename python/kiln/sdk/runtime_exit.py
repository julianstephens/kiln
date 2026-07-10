from dataclasses import dataclass
from enum import StrEnum

from kiln.protocol.pending import InflightRequestDisposition


class RuntimeFinalExitClass(StrEnum):
    """Represents the final exit class of a runtime process."""

    GRACEFUL_EXIT = "graceful_exit"
    PROTOCOL_EOF = "protocol_eof"
    STARTUP_FAILURE = "startup_failure"
    INITIALIZE_FAILURE = "initialize_failure"
    UNEXPECTED_EXIT = "unexpected_exit"
    FORCED_KILL = "forced_kill"
    CRASH = "crash"


@dataclass(frozen=True)
class RuntimeExitStatus:
    """Represents the exit status of a runtime process."""

    expected: bool
    timeout: bool
    returncode: int | None
    signal: int | None
    stderr_tail: str
    final_class: RuntimeFinalExitClass | None = None


@dataclass(frozen=True)
class RuntimeConnectionFailure:
    """Represents a failure of a runtime connection."""

    in_flight: tuple[InflightRequestDisposition, ...]


class StderrTailBuffer:
    """A buffer that keeps the last N bytes of stderr output from a runtime process."""

    _max_bytes: int
    _buf: bytearray

    def __init__(self, max_bytes: int = 16_384):
        self._max_bytes = max_bytes
        self._buf = bytearray()

    def append(self, data: bytes) -> None:
        """Append data to the buffer, keeping only the last N bytes.

        Args:
            data: The data to append to the buffer.
        """
        self._buf.extend(data)
        if len(self._buf) > self._max_bytes:
            del self._buf[: len(self._buf) - self._max_bytes]

    def text(self) -> str:
        """Return the contents of the buffer as a UTF-8 string, replacing any invalid
        characters.

        Returns:
            A string representation of the buffer contents.
        """
        return self._buf.decode("utf-8", errors="replace")
