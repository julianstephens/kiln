import json
from typing import Any

from .errors import (
    EmbeddedNewlineInMessageError,
    FramingError,
    JsonRpcFrameExceedsSizeLimitError,
)

DEFAULT_MAX_MESSAGE_BYTES = 1 << 20
DEFAULT_PYDANTIC_DUMP_ARGS = {"mode": "json"}

type JsonObject = dict[str, Any]


def decode_frame(
    frame: bytes, max_message_bytes: int = DEFAULT_MAX_MESSAGE_BYTES
) -> JsonObject:
    """Decode a JSON-RPC frame.

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

    return data


def encode_frame(message: JsonObject) -> bytes:
    """Encode a JSON-RPC frame.

    Args:
        message: The JSON-RPC frame as a dictionary.

    Returns:
        The JSON-RPC frame as bytes.

    Raises:
        EmbeddedNewlineInMessageError: If the frame contains an embedded newline.
    """
    data = json.dumps(
        message,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")

    if b"\n" in data:
        raise EmbeddedNewlineInMessageError

    return data + b"\n"
