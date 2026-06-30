import json

import pytest

from kiln.protocol.errors import (
    EmbeddedNewlineInMessageError,
    FramingError,
    JsonRpcFrameExceedsSizeLimitError,
)
from kiln.protocol.framing import decode_frame


def test_decode_frame_rejects_oversized_bytes() -> None:
    with pytest.raises(JsonRpcFrameExceedsSizeLimitError):
        decode_frame(b"{}", max_message_bytes=1)


def test_decode_frame_rejects_embedded_newline() -> None:
    with pytest.raises(EmbeddedNewlineInMessageError):
        decode_frame(b'{"jsonrpc":"2.0"}\n')


def test_decode_frame_rejects_malformed_json() -> None:
    with pytest.raises(FramingError, match="invalid JSON-RPC frame"):
        decode_frame(b'{"jsonrpc":"2.0"')


def test_decode_frame_rejects_non_object_json() -> None:
    with pytest.raises(FramingError, match="must be a JSON object"):
        decode_frame(json.dumps(["not", "an", "object"]).encode())


def test_decode_frame_returns_valid_json_object_unchanged() -> None:
    raw = {"jsonrpc": "2.0", "id": "1", "method": "repository.search", "params": {}}
    encoded = json.dumps(raw).encode()

    assert decode_frame(encoded) == raw
