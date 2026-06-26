class FramingError(RuntimeError):
    """Raised when a framing error occurs in the protocol."""

    def __init__(self, message: str) -> None:
        super().__init__(message)


class ProtocolMessageExceedsSizeLimitError(FramingError):
    """Raised when a protocol message exceeds the size limit."""

    def __init__(self, size: int, limit: int) -> None:
        super().__init__(f"protocol message size {size} exceeds limit {limit}")


class RuntimeStreamClosedError(EOFError):
    """Raised when the runtime protocol stream is closed unexpectedly."""

    def __init__(self) -> None:
        super().__init__("runtime protocol stream closed")
