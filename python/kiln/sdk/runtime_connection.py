from dataclasses import dataclass
from enum import StrEnum

from kiln.protocol.jsonrpc import (
    JsonRpcErrorResponse,
    JsonRpcRequest,
    JsonRpcSuccessResponse,
    new_request_id,
)
from kiln.protocol.pending import InflightDisposition, InflightRequestDisposition
from kiln.protocol.stdio import BufferedByteReceiveStream, Peer
from kiln.schemas import COMPATIBILITY_MAJOR, SCHEMA_SET_VERSION
from kiln.schemas.runtime import RuntimeError as KilnRuntimeError
from kiln.schemas.runtime import (
    RuntimeHealthResult,
    RuntimeInitializeRequestPayload,
    RuntimeInitializeResult,
    RuntimeShutdownRequestPayload,
    RuntimeShutdownResult,
)
from kiln.schemas.runtime.initialize_request_payload import Client as RuntimeClient

from . import PACKAGE_NAME, __version__
from ._runtime_os.win32 import ServerProcess
from .errors import RuntimeMethodError, RuntimeProcessError
from .runtime_exit import StderrTailBuffer

RUNTIME_PROTOCOL_VERSION = "2026-07-01"


@dataclass
class ShutdownConfig:
    grace_period_seconds: int
    cancel_in_flight_requests: bool


DefaultShutdownConfig = ShutdownConfig(
    grace_period_seconds=30, cancel_in_flight_requests=True
)


class RuntimeConnectionState(StrEnum):
    """Represents the state of a connection to a runtime process."""

    STARTING = "starting"
    READY = "ready"
    DRAINING = "draining"
    EXITED = "exited"
    FAILED = "failed"


class RuntimeStdioConnection:
    """Represents a connection to a runtime process over standard input and
    output streams."""

    peer: Peer
    process: ServerProcess

    _shutdown_config: ShutdownConfig

    _state: RuntimeConnectionState

    _stderr_tail: StderrTailBuffer

    def __init__(
        self,
        process: ServerProcess,
        shutdown_config: ShutdownConfig,
        state: RuntimeConnectionState = RuntimeConnectionState.EXITED,
        stderr_tail: StderrTailBuffer | None = None,
    ) -> None:
        self.process = process
        if not process.stdin:
            raise RuntimeProcessError(message="runtime process stdin is unavailable")
        if not process.stdout:
            raise RuntimeProcessError(message="runtime process stdout is unavailable")
        self.peer = Peer(
            stdin=process.stdin,
            stdout=BufferedByteReceiveStream(process.stdout),
        )
        self._shutdown_config = shutdown_config
        self._state = state
        self._stderr_tail = stderr_tail or StderrTailBuffer()

    def mark_failed(self) -> None:
        """Mark the connection as failed. Idempotent and sticky."""
        if self._state != RuntimeConnectionState.FAILED:
            self._state = RuntimeConnectionState.FAILED

    @property
    def state(self) -> RuntimeConnectionState:
        """The current state of the connection to the runtime process."""
        return self._state

    @state.setter
    def state(self, value: RuntimeConnectionState) -> None:
        if self._state == RuntimeConnectionState.FAILED:
            return
        self._state = value

    def inflight_disposition(
        self, disposition: InflightDisposition = "unknown"
    ) -> tuple[InflightRequestDisposition, ...]:
        """Return the disposition of all inflight requests in the connection's peer.

        Args:
            disposition: The disposition to assign to the inflight requests. Defaults to
                unknown.

        Returns:
            Tuple of `InflightRequestDisposition` instances representing the disposition
                of all inflight requests.
        """
        return self.peer._pending_requests.inflight_disposition(disposition)

    async def drain_stderr(self) -> None:
        """Drain the standard error stream of the runtime process and store the output
        in memory for later retrieval. This method reads from the standard error stream
        in chunks and appends the data to an internal buffer until the stream is closed
        or no more data is available.
        """
        stderr = getattr(self.process, "stderr", None)
        if stderr is None:
            return

        try:
            while True:
                chunk = await stderr.receive(4096)
                if not chunk:
                    return
                self._stderr_tail.append(chunk)
        except Exception:
            return

    async def initialize(self) -> RuntimeInitializeResult:
        """Initialize a connection to a runtime process over standard input and
        output streams.

        Returns:
            A `RuntimeInitializeResult` instance representing the initialization
                result.
        """
        params = RuntimeInitializeRequestPayload.model_validate(
            {
                "protocol_version": RUNTIME_PROTOCOL_VERSION,
                "schema_set_version": SCHEMA_SET_VERSION,
                "compatibility_major": COMPATIBILITY_MAJOR,
                "client": RuntimeClient(name=PACKAGE_NAME, version=__version__),
            }
        )

        res = await self.peer.request(
            JsonRpcRequest(
                id=new_request_id(),
                method="runtime.initialize",
                params=params.root.model_dump(),
            )
        )
        if isinstance(res, JsonRpcRequest):
            raise RuntimeProcessError(
                message=(
                    "runtime process returned an unexpected request "
                    "instead of a response"
                )
            )
        if isinstance(res, JsonRpcErrorResponse):
            raise _runtime_method_error(method="runtime.initialize", response=res)
        if isinstance(res, JsonRpcSuccessResponse):
            return RuntimeInitializeResult.model_validate(res.result)

        raise RuntimeProcessError(
            message="runtime process returned an unexpected response type"
        )

    async def health(self) -> RuntimeHealthResult:
        """Check the health of the runtime process.

        Returns:
            A `RuntimeHealthResult` instance representing the health check result.
        """
        res = await self.peer.request(
            JsonRpcRequest(id=new_request_id(), method="runtime.health")
        )

        if isinstance(res, JsonRpcRequest):
            raise RuntimeProcessError(
                message=(
                    "runtime process returned an unexpected request "
                    "instead of a response"
                )
            )
        if isinstance(res, JsonRpcErrorResponse):
            raise _runtime_method_error(method="runtime.health", response=res)
        if isinstance(res, JsonRpcSuccessResponse):
            health_res = RuntimeHealthResult.model_validate(res.result)

            if health_res.root.draining:
                self._state = RuntimeConnectionState.DRAINING
            elif health_res.root.ready:
                self._state = RuntimeConnectionState.READY
            elif health_res.root.shutdown:
                self._state = RuntimeConnectionState.EXITED
            else:
                # Not ready, not draining, not shutdown: still initializing
                self._state = RuntimeConnectionState.STARTING

            return health_res

        raise RuntimeProcessError(
            message="runtime process returned an unexpected response type"
        )

    async def shutdown(self) -> RuntimeShutdownResult:
        """Shutdown the runtime process gracefully.

        Returns:
            The result of the shutdown request as a `RuntimeShutdownResult` instance.
        """
        cancel_in_flight = self._shutdown_config.cancel_in_flight_requests
        params = RuntimeShutdownRequestPayload.model_validate(
            {
                "grace_period_seconds": self._shutdown_config.grace_period_seconds,
                "cancel_in_flight_requests": cancel_in_flight,
                "reason": "caller_requested",
            }
        )
        res = await self.peer.request(
            JsonRpcRequest(
                id=new_request_id(),
                method="runtime.shutdown",
                params=params.root.model_dump(),
            )
        )
        if isinstance(res, JsonRpcRequest):
            raise RuntimeProcessError(
                message=(
                    "runtime process returned an unexpected request "
                    "instead of a response"
                )
            )
        if isinstance(res, JsonRpcErrorResponse):
            raise _runtime_method_error(method="runtime.shutdown", response=res)
        if isinstance(res, JsonRpcSuccessResponse):
            self._state = RuntimeConnectionState.DRAINING
            return RuntimeShutdownResult.model_validate(res.result)

        raise RuntimeProcessError(
            message="runtime process returned an unexpected response type"
        )


def _runtime_method_error(
    method: str, response: JsonRpcErrorResponse
) -> RuntimeMethodError:
    return RuntimeMethodError(
        method=method,
        response=response,
        kiln_error=KilnRuntimeError.model_validate(response.error.data or {}),
    )
