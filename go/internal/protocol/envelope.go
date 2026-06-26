package protocol

import (
	"encoding/json"
	"time"
)

type Request struct {
	ProtocolVersion string          `json:"protocol_version"`
	RequestID       string          `json:"request_id"`
	Operation       string          `json:"operation"`
	CorrelationID   string          `json:"correlation_id,omitempty"`
	Deadline        *time.Time      `json:"deadline,omitempty"`
	Payload         json.RawMessage `json:"payload"`
}

type Response struct {
	ProtocolVersion string          `json:"protocol_version"`
	RequestID       string          `json:"request_id"`
	Operation       string          `json:"operation"`
	Status          string          `json:"status"`
	Result          json.RawMessage `json:"result,omitempty"`
	Error           *Error          `json:"error,omitempty"`
}
