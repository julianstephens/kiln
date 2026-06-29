from typing import Any, Literal

from anyio.abc import ByteSendStream
from anyio.streams.buffered import BufferedByteReceiveStream, IncompleteRead
from pydantic import BaseModel

from .errors import (
    EmbeddedNewlineInMessageError,
    FramingError,
    InvalidJsonRpcFrameError,
    RuntimeStreamClosedError,
)
from .framing import DEFAULT_MAX_MESSAGE_BYTES, validate_frame


class JsonRpcRequest(BaseModel):
    jsonrpc: Literal["2.0"]
    id: str | int
    method: str
    params: dict[str, Any] | None = None


class JsonRpcSuccessResponse(BaseModel):
    jsonrpc: Literal["2.0"]
    id: str | int
    result: dict[str, Any]


class JsonRpcErrorObject(BaseModel):
    code: int
    message: str
    data: dict[str, Any] | None = None


class JsonRpcErrorResponse(BaseModel):
    jsonrpc: Literal["2.0"]
    id: str | int | None
    error: JsonRpcErrorObject


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

    async def _read_line(self) -> bytes:
        """Read a line from the standard output stream.

        Returns:
            bytes: The line read from the stream.
        """
        try:
            return await self._stdout.receive_until(b"\n", self._max_message_bytes)
        except IncompleteRead as e:
            raise RuntimeStreamClosedError from e
        except Exception as e:
            raise FramingError(message=f"failed to read line from stdout: {e}") from e

    async def _write_line(self, line: bytes) -> None:
        """Write a line to the standard input stream.

        Args:
            line: The line to write to the stream.
        """
        await self._stdin.send(line + b"\n")

    async def receive(self) -> JsonRpcSuccessResponse | JsonRpcErrorResponse:
        """Read a JSON-RPC frame from the standard output stream.

        Returns:
            JsonRpcSuccessResponse | JsonRpcErrorResponse: The validated JSON-RPC frame.

        Raises:
            EmbeddedNewlineInMessageError: If an embedded newline is found in the frame.
            RuntimeStreamClosedError: If the standard output stream is closed
            unexpectedly.
            FramingError: If the frame is invalid or does not conform to the JSON-RPC
            specification.
        """
        line = await self._read_line()
        if b"\n" in line:
            raise EmbeddedNewlineInMessageError
        if not line:
            raise RuntimeStreamClosedError
        data = validate_frame(line, self._max_message_bytes)
        if "result" in data:
            try:
                res = JsonRpcSuccessResponse.model_validate(data)
            except Exception as e:
                raise InvalidJsonRpcFrameError(
                    message=f"invalid JSON-RPC response frame: {e}"
                ) from e
            return res
        if "error" in data:
            try:
                err = JsonRpcErrorResponse.model_validate(data)
            except Exception as e:
                raise InvalidJsonRpcFrameError(
                    message=f"invalid JSON-RPC error frame: {e}"
                ) from e
            return err
        raise InvalidJsonRpcFrameError(
            message="received JSON-RPC frame without 'result' or 'error' field"
        )

    async def send(self, payload: bytes):
        """Send a JSON-RPC frame to the standard input stream.

        Args:
            payload: The JSON-RPC frame as bytes.

        Raises:
            EmbeddedNewlineInMessageError: If an embedded newline is found in the frame.
            FramingError: If the frame is invalid or does not conform to the JSON-RPC
            specification.
        """
        if b"\n" in payload:
            raise EmbeddedNewlineInMessageError
        data = validate_frame(payload, self._max_message_bytes)
        try:
            jsonrpc_req = JsonRpcRequest.model_validate(data)
        except Exception as e:
            raise InvalidJsonRpcFrameError(
                message=f"invalid JSON-RPC request frame: {e}"
            ) from e
        await self._write_line(jsonrpc_req.model_dump_json().encode())
