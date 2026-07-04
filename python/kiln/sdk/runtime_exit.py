from dataclasses import dataclass

from kiln.protocol.pending import InflightRequestDisposition


@dataclass(frozen=True)
class RuntimeExitStatus:
    """Represents the exit status of a runtime process."""

    expected: bool
    returncode: int | None
    signal: int | None
    stderr_tail: str


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
