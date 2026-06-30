package protocol

import (
	"bufio"
	"bytes"
	"context"
	"fmt"
	"io"
)

type Peer struct {
	in       io.Reader
	out      *bufio.Writer
	maxBytes int
}

// NewPeer creates a new Peer with the given input and output streams and maximum message size in bytes.
// The Peer can be used to send and receive JSON-RPC messages over the provided streams.
func NewPeer(in io.Reader, out io.Writer, maxBytes int) *Peer {
	return &Peer{
		in:       in,
		out:      bufio.NewWriter(out),
		maxBytes: maxBytes,
	}
}

// Receive reads a JSON-RPC message from the input stream, decodes it, and parses it into a strongly typed Message (Request, SuccessResponse, or ErrorResponse).
// It returns an error if the message cannot be read, decoded, or parsed.
func (p *Peer) Receive(ctx context.Context) (Message, error) {
	line := make([]byte, p.maxBytes+1)
	n, err := p.in.Read(line)
	if err != nil {
		if err == io.EOF {
			return nil, NewRuntimeStreamClosedError("input stream closed", false, nil)
		}
		return nil, NewReadStreamError("error reading from input stream: "+err.Error(), false, nil)
	}
	line = bytes.TrimSuffix(line[:n], []byte("\n"))

	if bytes.Contains(line, []byte("\n")) {
		return nil, ErrEmbeddedNewline
	}

	raw, err := DecodeFrame(line, p.maxBytes)
	if err != nil {
		return nil, err
	}

	return ParseMessage(raw)
}

// Send encodes a JSON-RPC message and writes it to the output stream.
// It returns an error if the message cannot be encoded or if there is an error writing to the stream.
func (p *Peer) Send(msg Message) error {
	raw, err := messageToJSONObject(msg)
	if err != nil {
		return err
	}

	frame, err := EncodeFrame(raw)
	if err != nil {
		return err
	}

	_, err = p.out.Write(frame)
	if err != nil {
		return err
	}

	return p.out.Flush()
}

func messageToJSONObject(msg Message) (JSONObject, error) {
	switch m := msg.(type) {
	case Request:
		return JSONObject{
			"jsonrpc": m.JSONRPC,
			"id":      m.ID.JSONValue(),
			"method":  m.Method,
			"params":  m.Params,
		}, nil
	case SuccessResponse:
		return JSONObject{
			"jsonrpc": m.JSONRPC,
			"id":      m.ID.JSONValue(),
			"result":  m.Result,
		}, nil
	case ErrorResponse:
		return JSONObject{
			"jsonrpc": m.JSONRPC,
			"id":      m.ID.JSONValue(),
			"error": map[string]any{
				"code":    m.Error.Code,
				"message": m.Error.Message,
				"data":    m.Error.Data,
			},
		}, nil
	default:
		return nil, NewFramingError(fmt.Errorf("unknown message type: %T", msg))
	}
}
