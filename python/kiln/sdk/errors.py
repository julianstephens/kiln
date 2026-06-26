class RepositoryError(Exception):
    """Base class for all repository errors."""

    pass


class RepositoryNotFoundError(RepositoryError):
    """Raised when a repository is not found."""

    def __init__(self, repository_path: str):
        super().__init__(f"repository not found: {repository_path}")


class TaskEmptyError(ValueError):
    """Raised when a task is empty."""

    def __init__(self) -> None:
        super().__init__("task must not be empty")


class RuntimeProcessError(RuntimeError):
    """Raised when a runtime process fails to start or run."""

    def __init__(self, message: str) -> None:
        super().__init__(f"runtime process error: {message}")


class StdinUnavailableError(RuntimeProcessError):
    """Raised when the runtime process stdin is unavailable."""

    def __init__(self) -> None:
        super().__init__("runtime stdin is unavailable")


class StdoutUnavailableError(RuntimeProcessError):
    """Raised when the runtime process stdout is unavailable."""

    def __init__(self) -> None:
        super().__init__("runtime stdout is unavailable")


class MissingRuntimeBinaryError(RuntimeProcessError):
    """Raised when the runtime binary is missing."""

    def __init__(self) -> None:
        super().__init__("runtime binary is missing")
