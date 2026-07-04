from kiln.sdk.runtime_exit import InflightRequestDisposition


class FramingError(RuntimeError):
    """Raised when a framing error occurs in the protocol."""

    def __init__(self, message: str) -> None:
        super().__init__(message)


class JsonRpcFrameExceedsSizeLimitError(FramingError):
    """Raised when a JSON-RPC frame exceeds the size limit."""

    def __init__(self, size: int, limit: int) -> None:
        super().__init__(f"JSON-RPC frame size {size} exceeds limit {limit}")


class RuntimeStreamClosedError(EOFError):
    """Raised when the runtime protocol stream is closed unexpectedly."""

    def __init__(self) -> None:
        super().__init__("runtime protocol stream closed")


class EmbeddedNewlineInMessageError(ValueError):
    """Raised when an embedded newline is found in a protocol message."""

    def __init__(self) -> None:
        super().__init__("embedded newline in JSON-RPC frame")


class InvalidJsonRpcFrameError(FramingError):
    """Raised when a JSON-RPC frame is invalid or does not conform to the
    specification."""

    def __init__(self, message: str) -> None:
        super().__init__(f"invalid JSON-RPC frame: {message}")


class UnsupportedMethodError(FramingError):
    """Raised when a JSON-RPC method is not supported by the protocol."""

    def __init__(self, method: str) -> None:
        super().__init__(f"unsupported JSON-RPC method: {method}")


class KilnPayloadValidationError(FramingError):
    """Raised when a Kiln payload is invalid or does not conform to the schema."""

    def __init__(self, method: str, part: str, details: str) -> None:
        super().__init__(
            f"invalid Kiln payload: method={method}, part={part}, details={details}"
        )


class UnexpectedJsonRpcMessageError(RuntimeError):
    """Raised when an unexpected JSON-RPC message is received."""

    def __init__(self, message: str) -> None:
        super().__init__(f"unexpected JSON-RPC message: {message}")


class JsonRpcResponseIdMismatchError(RuntimeError):
    """Raised when a JSON-RPC response ID does not match the expected request ID."""

    def __init__(
        self, expected_id: str | int | None, received_id: str | int | None
    ) -> None:
        super().__init__(
            (
                f"JSON-RPC response ID mismatch: expected {expected_id}, "
                f"received {received_id}"
            )
        )


class RuntimeConnectionClosedError(RuntimeError):
    def __init__(
        self,
        message: str = "runtime connection closed",
        in_flight: tuple[InflightRequestDisposition, ...] = (),
    ) -> None:
        self.in_flight = in_flight
        super().__init__(message)


class RuntimeProcessExitedError(RuntimeConnectionClosedError):
    def __init__(self, returncode: int | None = None) -> None:
        super().__init__(
            f"runtime process exited unexpectedly: returncode={returncode}"
        )
        self.returncode = returncode
