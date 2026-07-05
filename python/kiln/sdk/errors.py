from typing import TYPE_CHECKING

from kiln.protocol.jsonrpc import JsonRpcErrorResponse
from kiln.schemas.runtime import RuntimeError as KilnRuntimeError

if TYPE_CHECKING:
    from .runtime_exit import InflightRequestDisposition, RuntimeExitStatus


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


class RuntimeMethodError(RuntimeProcessError):
    """Raised when a runtime method call fails."""

    def __init__(
        self, method: str, response: JsonRpcErrorResponse, kiln_error: KilnRuntimeError
    ) -> None:
        self.method = method
        self.response = response
        self.jsonrpc_code = response.error.code
        self.message = response.error.message
        self.error_data = response.error.data
        self.kiln_error = kiln_error
        super().__init__(
            f"runtime method error: method={method}, "
            f"jsonrpc_code={response.error.code}, "
            f"message={response.error.message}"
        )


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


class RuntimeProcessExitedError(RuntimeProcessError):
    def __init__(
        self,
        *,
        exit_status: "RuntimeExitStatus",
        in_flight: tuple["InflightRequestDisposition", ...],
    ) -> None:
        self.exit_status = exit_status
        self.in_flight = in_flight
        super().__init__(
            (
                "runtime process exited unexpectedly "
                f"returncode={exit_status.returncode}, "
                f"signal={exit_status.signal}"
            )
        )
