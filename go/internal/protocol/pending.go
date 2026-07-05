package protocol

import "sync"

type PendingRequest struct {
	ID     string
	Method string
}

type PendingRequests struct {
	mu    sync.Mutex
	byID  map[string]PendingRequest
	count int64
}

// IDKey returns the string representation of the ID, or an error if the ID is not a string.
func IDKey(id ID) (string, error) {
	if id.String != nil {
		return *id.String, nil
	}
	return "", NewInvalidIDError("ID must be a string", false, nil)
}

func NewPendingRequests() *PendingRequests {
	return &PendingRequests{
		byID: make(map[string]PendingRequest),
	}
}

func (p *PendingRequests) Add(id string, method string) {
	p.mu.Lock()
	defer p.mu.Unlock()
	if _, ok := p.byID[id]; !ok {
		p.count++
	}

	p.byID[id] = PendingRequest{
		ID:     id,
		Method: method,
	}
}

func (p *PendingRequests) Pop(id string) (PendingRequest, bool) {
	p.mu.Lock()
	defer p.mu.Unlock()
	req, ok := p.byID[id]
	if ok {
		delete(p.byID, id)
		p.count--
	}
	return req, ok
}

func (p *PendingRequests) Count() int64 {
	p.mu.Lock()
	defer p.mu.Unlock()
	return p.count
}

// ValidateResponseAgainstPendingRequest validates a JSON-RPC response against a pending request.
// It checks that the response corresponds to the pending request's method and validates the result or error data against the expected schema.
// If the response is invalid or does not match the pending request, it returns an error.
func ValidateResponseAgainstPendingRequest(req PendingRequest, response Message) error {
	method := req.Method
	spec, ok := KilnMethods[method]
	if !ok {
		return NewInvalidJSONRPCRequestError("unsupported method: "+method, false, nil)
	}
	switch resp := response.(type) {
	case SuccessResponse:
		if spec.ValidateResult == nil {
			return nil
		}
		_, err := spec.ValidateResult(resp.Result)
		if err != nil {
			return NewInvalidJSONRPCRequestError("invalid result: "+err.Error(), false, nil)
		}
		return nil
	case ErrorResponse:
		// Error data is already validated during message parsing,
		// so no additional validation is needed here.
	default:
		return NewInvalidJSONRPCRequestError("unexpected response type", false, nil)
	}
	return nil
}
