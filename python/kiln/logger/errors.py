class LoggerError(ValueError):
    """Base class for logger-related errors."""

    def __init__(self, message: str) -> None:
        super().__init__(message)


class UnsupportedLogLevelError(LoggerError):
    """Raised when an unsupported logger level is used."""

    def __init__(self, level: str) -> None:
        super().__init__(f"Unsupported logger level: {level!r}")


class UnsupportedLogFormatError(LoggerError):
    """Raised when an unsupported logger format is used."""

    def __init__(self, format: str) -> None:
        super().__init__(f"Unsupported logger format: {format!r}")


class UnsupportedLogSinkKindError(LoggerError):
    """Raised when an unsupported log sink kind is used."""

    def __init__(self, kind: str) -> None:
        super().__init__(f"Unsupported log sink kind: {kind!r}")
