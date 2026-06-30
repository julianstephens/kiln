from typing import Any, Literal

from pydantic import BaseModel, ConfigDict

from .errors import InvalidJsonRpcFrameError


class JsonRpcRequest(BaseModel):
    """A JSON-RPC request message."""

    model_config = ConfigDict(extra="forbid")

    jsonrpc: Literal["2.0"]
    id: str | int
    method: str
    params: dict[str, Any] | None = None


class JsonRpcSuccessResponse(BaseModel):
    """A JSON-RPC success response message."""

    model_config = ConfigDict(extra="forbid")

    jsonrpc: Literal["2.0"]
    id: str | int
    result: dict[str, Any]


class JsonRpcErrorObject(BaseModel):
    """A JSON-RPC error object."""

    model_config = ConfigDict(extra="forbid")

    code: int
    message: str
    data: dict[str, Any] | None = None


class JsonRpcErrorResponse(BaseModel):
    """A JSON-RPC error response message."""

    model_config = ConfigDict(extra="forbid")

    jsonrpc: Literal["2.0"]
    id: str | int | None
    error: JsonRpcErrorObject


type JsonRpcMessage = JsonRpcRequest | JsonRpcSuccessResponse | JsonRpcErrorResponse


def parse_jsonrpc_message(raw: dict[str, Any]) -> JsonRpcMessage:
    """Parse a raw JSON-RPC message into a validated Pydantic model.

    Args:
        raw: The raw JSON-RPC message as a dictionary.

    Returns:
        The validated Pydantic model instance.

    Raises:
        InvalidJsonRpcFrameError: If the raw message is invalid or does not conform to
            the JSON-RPC specification.
    """
    if raw.get("jsonrpc") != "2.0":
        raise InvalidJsonRpcFrameError(message="missing or unsupported 'jsonrpc' field")

    has_method = "method" in raw
    has_params = "params" in raw
    has_result = "result" in raw
    has_error = "error" in raw

    if has_params and not has_method:
        raise InvalidJsonRpcFrameError(
            message="invalid JSON-RPC frame: 'params' field without 'method'"
        )

    if has_method:
        if has_result or has_error:
            raise InvalidJsonRpcFrameError(
                message=(
                    "invalid JSON-RPC frame: 'method' field with 'result' or 'error'"
                )
            )

        try:
            return JsonRpcRequest.model_validate(raw)
        except Exception as e:
            raise InvalidJsonRpcFrameError(str(e)) from e

    if has_result and has_error:
        raise InvalidJsonRpcFrameError(
            message=(
                "invalid JSON-RPC frame: 'result' and "
                "'error' fields are mutually exclusive"
            )
        )

    if has_result:
        try:
            return JsonRpcSuccessResponse.model_validate(raw)
        except Exception as e:
            raise InvalidJsonRpcFrameError(str(e)) from e

    if has_error:
        try:
            return JsonRpcErrorResponse.model_validate(raw)
        except Exception as e:
            raise InvalidJsonRpcFrameError(str(e)) from e

    raise InvalidJsonRpcFrameError(
        message=(
            "invalid JSON-RPC frame: must contain either 'method', "
            "'result', or 'error' field"
        )
    )
