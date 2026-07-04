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
)
from kiln.schemas.runtime.initialize_request_payload import Client as RuntimeClient

from . import PACKAGE_NAME, __version__
from ._runtime_os.win32 import ServerProcess
from .errors import RuntimeMethodError, RuntimeProcessError
from .runtime_exit import StderrTailBuffer

RUNTIME_PROTOCOL_VERSION = "2026-07-01"


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

    _state: RuntimeConnectionState

    _stderr_tail: StderrTailBuffer

    def __init__(
        self,
        process: ServerProcess,
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
            raise RuntimeMethodError(
                method="runtime.initialize",
                jsonrpc_code=res.error.code,
                message=res.error.message,
                kiln_error=KilnRuntimeError.model_validate(res.error.data or {}),
            )
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
            raise RuntimeMethodError(
                method="runtime.health",
                jsonrpc_code=res.error.code,
                message=res.error.message,
                kiln_error=KilnRuntimeError.model_validate(res.error.data or {}),
            )
        if isinstance(res, JsonRpcSuccessResponse):
            health_res = RuntimeHealthResult.model_validate(res.result)

            if health_res.root.draining:
                self._state = RuntimeConnectionState.DRAINING
            elif health_res.root.ready:
                self._state = RuntimeConnectionState.READY
            else:
                # got a response, so connection is up but not ready
                self._state = RuntimeConnectionState.EXITED

            return health_res

        raise RuntimeProcessError(
            message="runtime process returned an unexpected response type"
        )
