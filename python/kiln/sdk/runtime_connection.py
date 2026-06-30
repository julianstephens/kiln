from pydantic import BaseModel

from kiln.protocol.stdio_jsonrpc import BufferedByteReceiveStream, StdioJsonRpcPeer

from ._runtime_os.win32 import ServerProcess
from .errors import RuntimeProcessError


class RuntimeInitializationResult(BaseModel):
    """Represents the result of initializing a connection to a runtime process."""

    initialized: bool


class RuntimeStdioConnection:
    """Represents a connection to a runtime process over standard input and
    output streams."""

    def __init__(self, process: ServerProcess):
        self.process = process
        if not process.stdin:
            raise RuntimeProcessError(message="runtime process stdin is unavailable")
        if not process.stdout:
            raise RuntimeProcessError(message="runtime process stdout is unavailable")
        self.peer = StdioJsonRpcPeer(
            stdin=process.stdin,
            stdout=BufferedByteReceiveStream(process.stdout),
        )

    async def initialize(self, process: ServerProcess) -> RuntimeInitializationResult:
        """Initialize a connection to a runtime process over standard input and
        output streams.

        Args:
            process: The runtime process to connect to.

        Returns:
            A `RuntimeInitializationResult` instance representing the initialization
                result.
        """
        ...
