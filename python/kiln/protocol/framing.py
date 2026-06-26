import json
from typing import Any, BinaryIO

from .errors import (
    FramingError,
    ProtocolMessageExceedsSizeLimitError,
    RuntimeStreamClosedError,
)

DEFAULT_MAX_MESSAGE_BYTES = 1 << 20


def write_message(stream: BinaryIO, message: dict[str, Any]) -> None:
    data = json.dumps(
        message,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")

    if len(data) > DEFAULT_MAX_MESSAGE_BYTES:
        raise ProtocolMessageExceedsSizeLimitError(len(data), DEFAULT_MAX_MESSAGE_BYTES)

    stream.write(data + b"\n")
    stream.flush()


def read_message(stream: BinaryIO) -> dict[str, Any]:
    line = stream.readline(DEFAULT_MAX_MESSAGE_BYTES + 1)

    if not line:
        raise RuntimeStreamClosedError

    if len(line) > DEFAULT_MAX_MESSAGE_BYTES:
        raise ProtocolMessageExceedsSizeLimitError(len(line), DEFAULT_MAX_MESSAGE_BYTES)

    try:
        value = json.loads(line)
    except json.JSONDecodeError as exc:
        raise FramingError(message="invalid JSON protocol message") from exc

    if not isinstance(value, dict):
        raise FramingError(message="protocol message must be an object")

    return value
