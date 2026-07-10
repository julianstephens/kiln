package protocol

import (
	"bufio"
	"bytes"
	"context"
	"io"
	"sync"
)

type Peer struct {
	mu sync.Mutex

	in    *bufio.Reader
	inRaw io.Reader
	out   *bufio.Writer

	inCh     chan ReceiveResult
	closeCh  chan struct{}
	readDone chan struct{}

	lastErr error

	maxBytes int
}

type ReceiveResult struct {
	Msg Message
	Err error
}

const (
	// Buffer size for the receive channel, allowing for some messages to be queued up before blocking the reader
	// goroutine. If inCh buffer is full the reader goroutine blocks on send; this prevents unbounded memory growth
	// but can stall the reader until the consumer drains the channel.If inCh buffer is full the reader goroutine
	// blocks on send; this prevents unbounded memory growth but can stall the reader until the consumer drains the channel.
	InChSize = 8
)

// NewPeer creates a new Peer with the given input and output streams and maximum message size.
// Receive operations will be performed in a separate goroutine, and results will be sent to the inCh channel.
// Reader goroutine blocks in ReadSlice and will only exit after the underlying reader is closed or returns an error;
// callers should call Close() to interrupt blocking reads if the underlying io.Reader implements io.Closer.
func NewPeer(in io.Reader, out io.Writer, maxBytes int) *Peer {
	p := &Peer{
		mu:       sync.Mutex{},
		in:       bufio.NewReader(in),
		inRaw:    in,
		out:      bufio.NewWriter(out),
		inCh:     make(chan ReceiveResult, InChSize),
		closeCh:  make(chan struct{}),
		readDone: make(chan struct{}),
		maxBytes: maxBytes,
	}
	go func() {
		defer close(p.inCh)
		defer close(p.readDone)
		var res ReceiveResult
		for {
			line, err := readLineBounded(context.Background(), p.in, p.maxBytes)
			if err != nil {
				p.setLastErr(err)
				res = ReceiveResult{Msg: nil, Err: err}
				select {
				case p.inCh <- res:
				case <-p.closeCh:
					return
				}
				return
			}

			payload := bytes.TrimSuffix(line, []byte("\n"))
			if len(payload) == 0 {
				res = ReceiveResult{Msg: nil, Err: NewInvalidJSONRPCFrameError("empty message")}
				select {
				case p.inCh <- res:
				case <-p.closeCh:
					return
				}
				continue
			}
			if bytes.Contains(payload, []byte("\n")) {
				res = ReceiveResult{Msg: nil, Err: ErrEmbeddedNewline}
				select {
				case p.inCh <- res:
				case <-p.closeCh:
					return
				}
				continue
			}
			raw, err := DecodeFrame(payload, p.maxBytes)
			if err != nil {
				res = ReceiveResult{Msg: nil, Err: err}
				select {
				case p.inCh <- res:
				case <-p.closeCh:
					return
				}
				continue
			}
			msg, err := ParseMessage(raw)
			res = ReceiveResult{Msg: msg, Err: err}
			select {
			case p.inCh <- res:
			case <-p.closeCh:
				return
			}
		}
	}()
	return p
}

// Receive reads a JSON-RPC message from the input stream and decodes it.
func (p *Peer) Receive(ctx context.Context) (Message, error) {
	select {
	case res, ok := <-p.inCh:
		if !ok {
			p.mu.Lock()
			err := p.lastErr
			p.mu.Unlock()
			if err != nil {
				return nil, err
			}
			return nil, NewRuntimeStreamClosedError("input stream closed", false, nil)
		}
		return res.Msg, res.Err
	case <-ctx.Done():
		return nil, ctx.Err()
	}
}

// Send encodes a JSON-RPC message and writes it to the output stream.
// It returns an error if the message cannot be encoded or if there is an error writing to the stream.
func (p *Peer) Send(msg Message) error {
	p.mu.Lock()
	defer p.mu.Unlock()

	raw, err := messageToJSON(msg)
	if err != nil {
		return err
	}

	frame, err := EncodeFrame(raw)
	if err != nil {
		return err
	}

	if _, err = p.out.Write(frame); err != nil {
		return err
	}

	return p.out.Flush()
}

// InChan returns the channel that receives messages from the Peer.
func (p *Peer) InChan() <-chan ReceiveResult { return p.inCh }

// Close closes the Peer, stopping any ongoing receive operations and closing the input stream if it implements io.Closer.
func (p *Peer) Close() error {
	select {
	case <-p.closeCh:
	default:
		close(p.closeCh)
	}

	if rc, ok := p.inRaw.(io.Closer); ok {
		_ = rc.Close()
	}

	<-p.readDone
	return nil
}

func (p *Peer) setLastErr(err error) {
	p.mu.Lock()
	defer p.mu.Unlock()
	p.lastErr = err
}

// LastErr returns the last error encountered by the Peer, if any.
func (p *Peer) LastErr() error {
	p.mu.Lock()
	defer p.mu.Unlock()
	return p.lastErr
}

func readLineBounded(ctx context.Context, r *bufio.Reader, maxBytes int) ([]byte, error) {
	var frame []byte

	for {
		select {
		case <-ctx.Done():
			return nil, ctx.Err()
		default:
		}
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
