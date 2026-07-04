from anyio.abc import ByteSendStream
from anyio.streams.buffered import (
    BufferedByteReceiveStream,
    DelimiterNotFound,
    IncompleteRead,
)

from .errors import (
    JsonRpcFrameExceedsSizeLimitError,
    JsonRpcResponseIdMismatchError,
    RuntimeConnectionClosedError,
    RuntimeStreamClosedError,
    UnexpectedJsonRpcMessageError,
)
from .framing import DEFAULT_MAX_MESSAGE_BYTES, decode_frame, encode_frame
from .jsonrpc import JsonRpcMessage, JsonRpcRequest, parse_jsonrpc_message
from .pending import InflightRequestDisposition, PendingRequests


class Peer:
    """A JSON-RPC peer that communicates over standard input and output streams."""

    _max_message_bytes: int
    _stdin: ByteSendStream
    _stdout: BufferedByteReceiveStream

    _pending_requests: PendingRequests

    def __init__(
        self,
        stdin: ByteSendStream,
        stdout: BufferedByteReceiveStream,
        max_message_bytes: int = DEFAULT_MAX_MESSAGE_BYTES,
    ) -> None:
        self._stdin = stdin
        self._stdout = stdout
        self._max_message_bytes = max_message_bytes
        self._pending_requests = PendingRequests()

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
        line = encode_frame(message.model_dump(mode="json", exclude_none=True))
        await self._stdin.send(line)

    async def request(self, message: JsonRpcRequest) -> JsonRpcMessage:
        """Send a JSON-RPC request to the peer and wait for a response.

        Args:
            message: The JSON-RPC request to send.

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
            UnexpectedJsonRpcMessageError: If the received message is unexpected.
            JsonRpcResponseIdMismatchError: If the received response ID does not match
                the expected request ID.
        """
        self._pending_requests.add(message.id, message.method)
        try:
            await self.send(message)
            res = await self.receive()

            if (
                isinstance(res, JsonRpcRequest)
                or res.id is None
                or res.id not in self._pending_requests
            ):
                raise UnexpectedJsonRpcMessageError(
                    message=res.model_dump_json(indent=2)
                )

            if res.id != message.id:
                raise JsonRpcResponseIdMismatchError(
                    expected_id=message.id, received_id=res.id
                )

            self._pending_requests.pop(res.id)
        except RuntimeStreamClosedError as exc:
            raise RuntimeConnectionClosedError(
                message=(
                    "runtime stream closed while waiting "
                    f"for response to {message.method}"
                ),
                in_flight=(
                    InflightRequestDisposition(
                        request_id=str(message.id),
                        method=message.method,
                        disposition="failed_connection_closed",
                    ),
                ),
            ) from exc
        else:
            return res
        finally:
            if message.id in self._pending_requests:
                self._pending_requests.pop(message.id)
