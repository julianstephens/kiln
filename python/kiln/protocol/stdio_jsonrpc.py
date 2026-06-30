from anyio.abc import ByteSendStream
from anyio.streams.buffered import (
    BufferedByteReceiveStream,
    DelimiterNotFound,
    IncompleteRead,
)

from .errors import (
    JsonRpcFrameExceedsSizeLimitError,
    RuntimeStreamClosedError,
)
from .framing import DEFAULT_MAX_MESSAGE_BYTES, decode_frame, encode_frame
from .jsonrpc import JsonRpcMessage, JsonRpcRequest, parse_jsonrpc_message


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
        self._stdin = stdin
        self._stdout = stdout
        self._max_message_bytes = max_message_bytes

    async def receive(self) -> JsonRpcMessage:
        """Receive a JSON-RPC message from the peer.

        Returns:
            The received JSON-RPC message as a validated Pydantic model.

        Raises:
            RuntimeStreamClosedError: If the stream is closed unexpectedly.
            JsonRpcFrameExceedsSizeLimitError: If the received frame exceeds the size
                limit.
            EmbeddedNewlineInMessageError: If the received frame contains an embedded
                newline.
            FramingError: If the received frame is invalid or does not conform to the
                JSON-RPC specification.
            InvalidJsonRpcFrameError: If the received message is invalid or does not
                conform to the JSON-RPC specification.
        """
        try:
            line = await self._stdout.receive_until(
                b"\n",
                self._max_message_bytes,
            )
        except DelimiterNotFound as exc:
            raise JsonRpcFrameExceedsSizeLimitError(
                size=self._max_message_bytes,
                limit=self._max_message_bytes,
            ) from exc
        except IncompleteRead as exc:
            raise RuntimeStreamClosedError from exc

        if not line:
            raise RuntimeStreamClosedError

        raw = decode_frame(line, self._max_message_bytes)
        return parse_jsonrpc_message(raw)

    async def send(self, message: JsonRpcRequest) -> None:
        """Send a JSON-RPC request to the peer.

        Args:
            message: The JSON-RPC request to send.

        Raises:
            RuntimeStreamClosedError: If the stream is closed unexpectedly.
        """
        line = encode_frame(message.model_dump(mode="json"))
        await self._stdin.send(line)
