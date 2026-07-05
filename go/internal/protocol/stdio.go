package protocol

import (
	"bufio"
	"bytes"
	"context"
	"io"
)

type Peer struct {
	in       *bufio.Reader
	out      *bufio.Writer
	maxBytes int
}

type ReceiveResult struct {
	Msg Message
	Err error
}

// NewPeer creates a new Peer with the given input and output streams and maximum message size in bytes.
// The Peer can be used to send and receive JSON-RPC messages over the provided streams.
func NewPeer(in io.Reader, out io.Writer, maxBytes int) *Peer {
	return &Peer{
		in:       bufio.NewReader(in),
		out:      bufio.NewWriter(out),
		maxBytes: maxBytes,
	}
}

// Receive reads a JSON-RPC message from the input stream, decodes it, and parses it into a strongly typed Message (Request, SuccessResponse, or ErrorResponse).
// It returns an error if the message cannot be read, decoded, or parsed.
func (p *Peer) Receive(ctx context.Context) (Message, error) {
	line, err := readLineBounded(p.in, p.maxBytes)
	if err != nil {
		return nil, err
	}
	payload := bytes.TrimSuffix(line, []byte("\n"))

	if len(payload) == 0 {
		return nil, NewInvalidJSONRPCFrameError("empty message")
	}

	if bytes.Contains(payload, []byte("\n")) {
		return nil, ErrEmbeddedNewline
	}

	raw, err := DecodeFrame(payload, p.maxBytes)
	if err != nil {
		return nil, err
	}

	return ParseMessage(raw)
}

// Send encodes a JSON-RPC message and writes it to the output stream.
// It returns an error if the message cannot be encoded or if there is an error writing to the stream.
func (p *Peer) Send(msg Message) error {
	raw, err := messageToJSON(msg)
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

// ReceiveCh starts a goroutine to receive a message from the Peer and returns a channel that will receive the result (message or error).
func (p *Peer) ReceiveCh(ctx context.Context) <-chan ReceiveResult {
	ch := make(chan ReceiveResult)
	go func() {
		msg, err := p.Receive(ctx)
		ch <- ReceiveResult{Msg: msg, Err: err}
		close(ch)
	}()
	return ch
}

func readLineBounded(r *bufio.Reader, maxBytes int) ([]byte, error) {
	var frame []byte

	for {
		chunk, err := r.ReadSlice('\n')
		frame = append(frame, chunk...)

		if len(frame) > maxBytes {
			return nil, NewFrameTooLargeError(len(frame), maxBytes)
		}

		if err == nil {
			return frame, nil
		}

		if err == bufio.ErrBufferFull {
			continue
		}

		if err == io.EOF {
			if len(frame) == 0 {
				return nil, NewRuntimeStreamClosedError("input stream closed", false, nil)
			}
			return nil, NewReadStreamError("partial frame before EOF", false, nil)
		}

		return nil, NewReadStreamError("error reading from input stream: "+err.Error(), false, nil)
	}
}
