package protocol

import (
	"bufio"
	"encoding/json"
	"fmt"
	"io"
)

const DefaultMaxMessageBytes = 1 << 20

type Decoder struct {
	scanner *bufio.Scanner
}

func NewDecoder(r io.Reader, maxBytes int) *Decoder {
	if maxBytes <= 0 {
		maxBytes = DefaultMaxMessageBytes
	}

	scanner := bufio.NewScanner(r)
	scanner.Buffer(make([]byte, 64*1024), maxBytes)

	return &Decoder{scanner: scanner}
}

func (d *Decoder) Decode(target any) error {
	if !d.scanner.Scan() {
		if err := d.scanner.Err(); err != nil {
			return err
		}
		return io.EOF
	}

	if err := json.Unmarshal(d.scanner.Bytes(), target); err != nil {
		return fmt.Errorf("decode protocol message: %w", err)
	}

	return nil
}

type Encoder struct {
	writer *bufio.Writer
}

func NewEncoder(w io.Writer) *Encoder {
	return &Encoder{writer: bufio.NewWriter(w)}
}

func (e *Encoder) Encode(value any) error {
	data, err := json.Marshal(value)
	if err != nil {
		return fmt.Errorf("encode protocol message: %w", err)
	}

	if _, err := e.writer.Write(append(data, '\n')); err != nil {
		return err
	}

	return e.writer.Flush()
}
