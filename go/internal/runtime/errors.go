package runtime

type Error struct {
	Code    string `json:"code"`
	Message string `json:"message"`
}

func (e *Error) Error() string {
	return e.Code + ": " + e.Message
}

const (
	CodeInputStreamMissing  = "input_stream_missing"
	CodeOutputStreamMissing = "output_stream_missing"
)

var (
	ErrInputStreamMissing = &Error{
		Code:    CodeInputStreamMissing,
		Message: "input stream is missing",
	}
	ErrOutputStreamMissing = &Error{
		Code:    CodeOutputStreamMissing,
		Message: "output stream is missing",
	}
)
