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

RUNTIME_PROTOCOL_VERSION = "2026-07-01"


class RuntimeStdioConnection:
    """Represents a connection to a runtime process over standard input and
    output streams."""

    peer: Peer
    process: ServerProcess

    def __init__(self, process: ServerProcess):
        self.process = process
        if not process.stdin:
            raise RuntimeProcessError(message="runtime process stdin is unavailable")
        if not process.stdout:
            raise RuntimeProcessError(message="runtime process stdout is unavailable")
        self.peer = Peer(
            stdin=process.stdin,
            stdout=BufferedByteReceiveStream(process.stdout),
        )

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
                params=params.model_dump(),
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
            return RuntimeHealthResult.model_validate(res.result)

        raise RuntimeProcessError(
            message="runtime process returned an unexpected response type"
        )
