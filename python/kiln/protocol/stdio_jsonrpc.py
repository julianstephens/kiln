from anyio.abc import ByteSendStream
from anyio.streams.buffered import BufferedByteReceiveStream

from .errors import EmbeddedNewlineInMessageError, RuntimeStreamClosedError
from .framing import DEFAULT_MAX_MESSAGE_BYTES, validate_frame


class StdioJsonRpcPeer:
    """A JSON-RPC peer that communicates over standard input and output streams."""

    _max_message_bytes: int
    _stdin: ByteSendStream
    _stdout: BufferedByteReceiveStream

    def __init__(
        self,
        stdin: ByteSendStream,
        stdout: BufferedByteReceiveStream,
        max_message_bytes: int = DEFAULT_MAX_MESSAGE_BYTES,
    ) -> None:
        self._max_message_bytes = max_message_bytes
        self._stdin = stdin
        self._stdout = stdout

    async def read_frame(self) -> bytes:
        """Read a JSON-RPC frame from the standard output stream.

        Returns:
            bytes: The validated JSON-RPC frame.

        Raises:
            EmbeddedNewlineInMessageError: If an embedded newline is found in the frame.
            RuntimeStreamClosedError: If the standard output stream is closed
            unexpectedly.
        """
        line = await self._stdout.receive_until(b"\n", self._max_message_bytes)
        if b"\n" in line:
            raise EmbeddedNewlineInMessageError
        if not line:
            raise RuntimeStreamClosedError
        data = validate_frame(line, self._max_message_bytes)
        return data.model_dump_json().encode("utf-8")

    async def send_frame(self, payload: bytes):
        """Send a JSON-RPC frame to the standard input stream.

        Args:
            payload: The JSON-RPC frame as bytes.

        Raises:
            EmbeddedNewlineInMessageError: If an embedded newline is found in the frame.
        """
        if b"\n" in payload:
            raise EmbeddedNewlineInMessageError
        data = validate_frame(payload, self._max_message_bytes)
        await self._stdin.send(data.model_dump_json().encode("utf-8") + b"\n")
