import json
from typing import Literal

from pydantic import BaseModel

from kiln.schemas import (
    ModelError,
    ModelGeneratePayload,
    ModelGenerateResult,
    RepositoryError,
    RepositoryOpenSessionRequestPayload,
    RepositorySearchRequestPayload,
    RepositorySearchResult,
    RepositorySession,
    RepositorySourceRequestPayload,
    RepositorySourceResult,
)

from .errors import (
    EmbeddedNewlineInMessageError,
    FramingError,
    JsonRpcFrameExceedsSizeLimitError,
)

DEFAULT_MAX_MESSAGE_BYTES = 1 << 20


SUPPORTED_SCHEMAS = {
    "repository.open_session": {
        "request_schema": RepositoryOpenSessionRequestPayload,
        "result_schema": RepositorySession,
        "error_schema": RepositoryError,
    },
    "repository.search": {
        "request_schema": RepositorySearchRequestPayload,
        "result_schema": RepositorySearchResult,
        "error_schema": RepositoryError,
    },
    "repository.get_source": {
        "request_schema": RepositorySourceRequestPayload,
        "result_schema": RepositorySourceResult,
        "error_schema": RepositoryError,
    },
    "model.generate": {
        "request_schema": ModelGeneratePayload,
        "result_schema": ModelGenerateResult,
        "error_schema": ModelError,
    },
}


class JsonRpcFrame(BaseModel):
    jsonrpc: str
    id: str | int
    method: str
    params: dict | None = None
    result: dict | None = None
    error: dict | None = None


def validate_frame(
    frame: bytes, max_message_bytes: int = DEFAULT_MAX_MESSAGE_BYTES
) -> JsonRpcFrame:
    """Validate a JSON-RPC frame.

    Args:
        frame: The JSON-RPC frame as bytes.
        max_message_bytes: The maximum allowed size of the frame in bytes.

    Returns:
        The validated JSON-RPC frame as a JsonRpcFrame object.

    Raises:
        JsonRpcFrameExceedsSizeLimitError: If the frame exceeds the size limit.
        EmbeddedNewlineInMessageError: If the frame contains an embedded newline.
        FramingError: If the frame is invalid or does not conform to the JSON-RPC
            specification.
    """
    if len(frame) > max_message_bytes:
        raise JsonRpcFrameExceedsSizeLimitError(len(frame), max_message_bytes)

    if b"\n" in frame:
        raise EmbeddedNewlineInMessageError

    try:
        data = json.loads(frame)
    except json.JSONDecodeError as e:
        raise FramingError(message=f"invalid JSON-RPC frame: {e}") from e

    if not isinstance(data, dict):
        raise FramingError(message="invalid JSON-RPC frame: must be a JSON object")

    allowed_fields = {"jsonrpc", "id", "method", "params", "result", "error"}
    for field in data:
        if field not in allowed_fields:
            raise FramingError(
                message=f"invalid JSON-RPC frame: unexpected field '{field}'"
            )

    jsonrpc_version = data.get("jsonrpc")
    if not jsonrpc_version:
        raise FramingError(
            message="invalid JSON-RPC frame: missing required field 'jsonrpc'"
        )
    if jsonrpc_version != "2.0":
        raise FramingError(
            message=(
                "invalid JSON-RPC frame: unsupported "
                f"jsonrpc version {jsonrpc_version}"
            )
        )

    if "id" not in data or data["id"] is None:
        raise FramingError(
            message="invalid JSON-RPC frame: missing required field 'id'"
        )
    request_id = data["id"]
    if not isinstance(request_id, str | int):
        raise FramingError(
            message="invalid JSON-RPC frame: field 'id' must be a string or number"
        )

    method = data.get("method")
    if not method:
        raise FramingError(
            message="invalid JSON-RPC frame: missing required field 'method'"
        )
    if not isinstance(method, str):
        raise FramingError(
            message="invalid JSON-RPC frame: field 'method' must be a string"
        )
    if method not in SUPPORTED_SCHEMAS:
        raise FramingError(
            message=f"invalid JSON-RPC frame: unsupported method '{method}'"
        )

    has_params = "params" in data
    has_result = "result" in data
    has_error = "error" in data

    payload_fields_set = sum([has_params, has_result, has_error])
    if payload_fields_set == 0:
        raise FramingError(
            message=(
                f"invalid JSON-RPC frame: no valid payload found "
                f"for method '{method}'"
            )
        )
    if has_params and (has_result or has_error):
        raise FramingError(
            message=(
                f"invalid JSON-RPC frame: cannot have both 'params' and "
                f"'result'/'error' for method '{method}'"
            )
        )
    if has_result and has_error:
        raise FramingError(
            message=(
                f"invalid JSON-RPC frame: cannot have both 'result' and "
                f"'error' for method '{method}'"
            )
        )

    validated_params = None
    validated_result = None
    validated_error = None

    if has_params and "request_schema" in SUPPORTED_SCHEMAS[method]:
        validated_params = validate_json(
            data_type="request",
            schema=SUPPORTED_SCHEMAS[method]["request_schema"],
            frame=data,
        )
    if has_result and "result_schema" in SUPPORTED_SCHEMAS[method]:
        validated_result = validate_json(
            data_type="response",
            schema=SUPPORTED_SCHEMAS[method]["result_schema"],
            frame=data,
        )
    if has_error and "error_schema" in SUPPORTED_SCHEMAS[method]:
        validated_error = validate_json(
            data_type="error",
            schema=SUPPORTED_SCHEMAS[method]["error_schema"],
            frame=data,
        )

    return JsonRpcFrame(
        jsonrpc=jsonrpc_version,
        id=request_id,
        method=method,
        params=validated_params.model_dump(round_trip=True)
        if validated_params
        else None,
        result=validated_result.model_dump(round_trip=True)
        if validated_result
        else None,
        error=validated_error.model_dump(round_trip=True) if validated_error else None,
    )


def validate_json(
    *,
    data_type: Literal["request", "response", "error"],
    schema: type[BaseModel],
    frame: dict,
) -> BaseModel:
    """Validate JSON-RPC frame against the given schema.

    Args:
        data_type: The type of the JSON-RPC frame, either "request", "response",
        or "error".
        schema: The Pydantic model class to validate against.
        frame: The JSON-RPC frame as a dictionary.

    Returns:
        The validated Pydantic model instance.

    Raises:
        FramingError: If the frame is invalid or does not conform to the schema.
    """
    data = None
    if data_type == "request":
        if "params" not in frame:
            raise FramingError(
                message=(
                    "invalid JSON-RPC frame: missing required field 'params' "
                    f"for method '{frame.get('method')}'"
                )
            )
        data = frame["params"]
    if data_type == "response":
        if "result" not in frame:
            raise FramingError(
                message=(
                    "invalid JSON-RPC frame: missing required field 'result' "
                    f"for method '{frame.get('method')}'"
                )
            )
        data = frame["result"]
    if data_type == "error":
        if "error" not in frame:
            raise FramingError(
                message=(
                    "invalid JSON-RPC frame: missing required field 'error' "
                    f"for method '{frame.get('method')}'"
                )
            )
        data = frame["error"]

    if not isinstance(data, dict):
        raise FramingError(
            message=(
                f"invalid JSON-RPC frame: {data_type} must be a JSON object "
                f"for method '{frame.get('method')}'"
            )
        )
    try:
        validated_data = schema.model_validate(data)
    except Exception as e:
        raise FramingError(
            message=(
                "invalid JSON-RPC frame: payload validation failed "
                f"for schema '{schema.__name__}': {e}"
            )
        ) from e
    else:
        return validated_data
