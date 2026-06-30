from typing import get_args

from kiln.protocol.jsonrpc import (
    DEFAULT_JSONRPC_VERSION,
    JsonRpcErrorResponse,
    JsonRpcRequest,
    JsonRpcSuccessResponse,
)
from kiln.protocol.stdio import BufferedByteReceiveStream, Peer
from kiln.schemas import COMPATIBILITY_MAJOR, SCHEMA_SET_VERSION
from kiln.schemas.runtime import (
    RuntimeHealthResult,
    RuntimeInitializeRequestPayload,
    RuntimeInitializeResult,
)
from kiln.schemas.runtime.initialize_request_payload import (
    Client as RuntimeClient,
)

from . import PACKAGE_NAME, __version__
from ._runtime_os.win32 import ServerProcess
from .errors import RuntimeProcessError


class RuntimeStdioConnection:
    """Represents a connection to a runtime process over standard input and
    output streams."""

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
                "protocol_version": get_args(DEFAULT_JSONRPC_VERSION)[0],
                "schema_set_version": SCHEMA_SET_VERSION,
                "compatibility_major": COMPATIBILITY_MAJOR,
                "client": RuntimeClient(name=PACKAGE_NAME, version=__version__),
            }
        )
        res = await self.peer.request(
            JsonRpcRequest(
                id="", method="runtime.initialize", params=params.model_dump()
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
            raise RuntimeProcessError(
                message=(
                    f"runtime process returned an error: {res.error.code} - "
                    f"{res.error.message}"
                )
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
        res = await self.peer.request(JsonRpcRequest(id="", method="runtime.health"))

        if isinstance(res, JsonRpcRequest):
            raise RuntimeProcessError(
                message=(
                    "runtime process returned an unexpected request "
                    "instead of a response"
                )
            )
        if isinstance(res, JsonRpcErrorResponse):
            raise RuntimeProcessError(
                message=(
                    f"runtime process returned an error: {res.error.code} - "
                    f"{res.error.message}"
                )
            )
        if isinstance(res, JsonRpcSuccessResponse):
            return RuntimeHealthResult.model_validate(res.result)

        raise RuntimeProcessError(
            message="runtime process returned an unexpected response type"
        )
