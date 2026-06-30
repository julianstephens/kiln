package protocol

import (
	"bytes"
	"encoding/json"
	"fmt"
)

const DefaultMaxMessageBytes = 1 << 20

type JSONObject map[string]any

// DecodeFrame decodes a JSON frame into a JSONObject. It returns an error if the frame is too large, contains a newline character, or is not valid JSON.
// The maxBytes parameter specifies the maximum allowed size of the frame in bytes.
func DecodeFrame(frame []byte, maxBytes int) (JSONObject, error) {
	if len(frame) > maxBytes {
		return nil, NewFrameTooLargeError(len(frame), maxBytes)
	}

	if bytes.Contains(frame, []byte("\n")) {
		return nil, ErrEmbeddedNewline
	}

	var value any
	if err := json.Unmarshal(frame, &value); err != nil {
		return nil, NewFramingError(err)
	}

	obj, ok := value.(map[string]any)
	if !ok {
		return nil, NewFramingError(fmt.Errorf("expected JSON object, got %T", value))
	}

	return obj, nil
}

// EncodeFrame encodes a JSON object into a frame, appending a newline character at the end.
// It returns an error if the object cannot be marshaled into JSON or if the resulting frame contains a newline character.
func EncodeFrame(obj JSONObject) ([]byte, error) {
	data, err := json.Marshal(obj)
	if err != nil {
		return nil, NewFramingError(err)
	}

	if bytes.Contains(data, []byte("\n")) {
		return nil, ErrEmbeddedNewline
	}

	return append(data, '\n'), nil
}
