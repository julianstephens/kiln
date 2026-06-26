def test_framing_error_message():
    from python.kiln.protocol.errors import FramingError

    error = FramingError(message="test message")
    assert str(error) == "test message"
