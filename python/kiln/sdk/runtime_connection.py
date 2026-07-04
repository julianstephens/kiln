from enum import StrEnum

from kiln.protocol.jsonrpc import (
    JsonRpcErrorResponse,
    JsonRpcRequest,
    JsonRpcSuccessResponse,
    new_request_id,
)
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
from .runtime_exit import InflightDisposition, InflightRequestDisposition

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

    _draining: bool
    _initialized: bool
    _ready: bool
    _shutdown: bool

    def __init__(self, process: ServerProcess, state: RuntimeConnectionState):
        self.process = process
        if not process.stdin:
            raise RuntimeProcessError(message="runtime process stdin is unavailable")
        if not process.stdout:
            raise RuntimeProcessError(message="runtime process stdout is unavailable")
        self.peer = Peer(
            stdin=process.stdin,
            stdout=BufferedByteReceiveStream(process.stdout),
        )
        match state:
            case RuntimeConnectionState.STARTING:
                self._draining = False
                self._initialized = False
                self._ready = False
                self._shutdown = False
            case RuntimeConnectionState.READY:
                self._draining = False
                self._initialized = True
                self._ready = True
                self._shutdown = False
            case RuntimeConnectionState.DRAINING:
                self._draining = True
                self._initialized = True
                self._ready = False
                self._shutdown = False
            case RuntimeConnectionState.EXITED:
                self._draining = False
                self._initialized = False
                self._ready = False
                self._shutdown = True
            case RuntimeConnectionState.FAILED:
                self._draining = False
                self._initialized = False
                self._ready = False
                self._shutdown = True

    @property
    def draining(self) -> bool:
        return self._draining

    @property
    def initialized(self) -> bool:
        return self._initialized

    @property
    def ready(self) -> bool:
        return self._ready

    @property
    def shutdown(self) -> bool:
        return self._shutdown

    def inflight_disposition(
        self, disposition: InflightDisposition = "unknown"
    ) -> tuple[InflightRequestDisposition, ...]:
        res = []
        for inflight_req in self.peer._pending_requests:
            res.append(
                InflightRequestDisposition(
                    request_id=str(inflight_req.id),
                    method=inflight_req.method,
                    disposition=disposition,
                )
            )
        return tuple(res)

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
            self._draining = health_res.root.draining
            self._initialized = health_res.root.initialized
            self._ready = health_res.root.ready
            self._shutdown = health_res.root.shutdown
            return health_res

        raise RuntimeProcessError(
            message="runtime process returned an unexpected response type"
        )
