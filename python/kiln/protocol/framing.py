import json

from .errors import (
    EmbeddedNewlineInMessageError,
    FramingError,
    JsonRpcFrameExceedsSizeLimitError,
)
from .method_validation import KILN_METHODS, validate_kiln_schema

DEFAULT_MAX_MESSAGE_BYTES = 1 << 20
DEFAULT_PYDANTIC_DUMP_ARGS = {"mode": "json"}


def validate_frame(
    frame: bytes, max_message_bytes: int = DEFAULT_MAX_MESSAGE_BYTES
) -> dict:
    """Validate a JSON-RPC frame.

    Args:
        frame: The JSON-RPC frame as bytes.
        max_message_bytes: The maximum allowed size of the frame in bytes.

    Returns:
        The validated JSON-RPC frame as a dictionary.

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
    if method is not None and not isinstance(method, str):
        raise FramingError(
            message="invalid JSON-RPC frame: field 'method' must be a string"
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

    validated_frame = {
        "jsonrpc": jsonrpc_version,
        "id": request_id,
    }
    if method is not None:
        validated_frame["method"] = method

    if has_params:
        if not method:
            raise FramingError(
                message="invalid JSON-RPC frame: missing required field 'method'"
            )
        if method not in KILN_METHODS:
            raise FramingError(
                message=f"invalid JSON-RPC frame: unsupported method '{method}'"
            )
        if not KILN_METHODS[method].params_model:
            raise FramingError(
                message=(
                    f"invalid JSON-RPC frame: method '{method}' does not "
                    "support a 'params' payload"
                )
            )
        validated_params = validate_kiln_schema(
            data_type="request",
            schema=KILN_METHODS[method].params_model,  # type: ignore[arg-type]
            frame=data,
        )
        validated_frame["params"] = validated_params.model_dump(
            **DEFAULT_PYDANTIC_DUMP_ARGS  # type: ignore
        )

    if has_result:
        if method is not None:
            if method not in KILN_METHODS:
                raise FramingError(
                    message=f"invalid JSON-RPC frame: unsupported method '{method}'"
                )
            if not KILN_METHODS[method].result_model:
                raise FramingError(
                    message=(
                        f"invalid JSON-RPC frame: method '{method}' does not "
                        "support a 'result' payload"
                    )
                )
            validated_result = validate_kiln_schema(
                data_type="response",
                schema=KILN_METHODS[method].result_model,  # type: ignore[arg-type]
                frame=data,
            )
            validated_frame["result"] = validated_result.model_dump(
                **DEFAULT_PYDANTIC_DUMP_ARGS  # type: ignore
            )
        else:
            if not isinstance(data.get("result"), dict):
                raise FramingError(
                    message="invalid JSON-RPC frame: response must be a JSON object"
                )
            validated_frame["result"] = data["result"]

    if has_error:
        error = data.get("error")
        if not isinstance(error, dict):
            raise FramingError(
                message="invalid JSON-RPC frame: error must be a JSON object"
            )
        if "code" not in error or "message" not in error:
            raise FramingError(
                message=(
                    "invalid JSON-RPC frame: error must include 'code' and "
                    "'message' fields"
                )
            )
        if not isinstance(error["code"], int):
            raise FramingError(
                message="invalid JSON-RPC frame: error.code must be an integer"
            )
        if not isinstance(error["message"], str):
            raise FramingError(
                message="invalid JSON-RPC frame: error.message must be a string"
            )

        validated_error = {
            "code": error["code"],
            "message": error["message"],
        }

        if "data" in error and error["data"] is not None:
            if not isinstance(error["data"], dict):
                raise FramingError(
                    message="invalid JSON-RPC frame: error.data must be a JSON object"
                )
            if method is not None:
                if method not in KILN_METHODS:
                    raise FramingError(
                        message=(
                            f"invalid JSON-RPC frame: unsupported method '{method}'"
                        )
                    )
                if not KILN_METHODS[method].error_data_model:
                    raise FramingError(
                        message=(
                            f"invalid JSON-RPC frame: method '{method}' does not "
                            "support error.data payload"
                        )
                    )
                validated_error_data = KILN_METHODS[
                    method
                ].error_data_model.model_validate(  # type: ignore[union-attr]
                    error["data"]
                )
                validated_error["data"] = validated_error_data.model_dump(
                    **DEFAULT_PYDANTIC_DUMP_ARGS  # type: ignore
                )
            else:
                validated_error["data"] = error["data"]

        validated_frame["error"] = validated_error

    return validated_frame
