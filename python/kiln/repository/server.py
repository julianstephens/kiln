from typing import Any, BinaryIO

from kiln.protocol.framing import read_message, write_message


class RepositoryServer:
    def __init__(
        self,
        *,
        input_stream: BinaryIO,
        output_stream: BinaryIO,
    ) -> None:
        self._input = input_stream
        self._output = output_stream

    def serve(self) -> None:
        while True:
            try:
                request = read_message(self._input)
            except EOFError:
                return

            operation = request.get("operation")

            if operation == "worker.health":
                result = {"status": "ready"}
            elif operation == "worker.shutdown":
                write_message(
                    self._output,
                    self._response(request, {"status": "stopping"}),
                )
                return
            else:
                write_message(
                    self._output,
                    self._error(request, "unknown_operation"),
                )
                continue

            write_message(
                self._output,
                self._response(request, result),
            )

    @staticmethod
    def _response(
        request: dict[str, Any],
        result: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            "protocol_version": request.get("protocol_version"),
            "request_id": request.get("request_id"),
            "operation": request.get("operation"),
            "status": "ok",
            "result": result,
        }

    @staticmethod
    def _error(
        request: dict[str, Any],
        code: str,
    ) -> dict[str, Any]:
        return {
            "protocol_version": request.get("protocol_version"),
            "request_id": request.get("request_id"),
            "operation": request.get("operation"),
            "status": "error",
            "error": {
                "code": code,
                "message": code.replace("_", " "),
                "retryable": False,
            },
        }
