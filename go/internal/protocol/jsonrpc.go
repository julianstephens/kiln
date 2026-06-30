package protocol

import "math"

const DEFAULT_JSONRPC_VERSION = "2.0"

type ID struct {
	String *string
	Number *int64
	Null   bool
}

func (id ID) JSONValue() any {
	switch {
	case id.String != nil:
		return *id.String
	case id.Number != nil:
		return *id.Number
	case id.Null:
		return nil
	default:
		return nil
	}
}

type Request struct {
	JSONRPC string         `json:"jsonrpc"`
	ID      ID             `json:"id"`
	Method  string         `json:"method"`
	Params  map[string]any `json:"params,omitempty"`
}

type SuccessResponse struct {
	JSONRPC string         `json:"jsonrpc"`
	ID      ID             `json:"id"`
	Result  map[string]any `json:"result"`
}

type ErrorObject struct {
	Code    int            `json:"code"`
	Message string         `json:"message"`
	Data    map[string]any `json:"data,omitempty"`
}

type ErrorResponse struct {
	JSONRPC string      `json:"jsonrpc"`
	ID      ID          `json:"id"`
	Error   ErrorObject `json:"error"`
}

type Message interface {
	isJsonRPCMessage()
}

func (Request) isJsonRPCMessage()         {}
func (SuccessResponse) isJsonRPCMessage() {}
func (ErrorResponse) isJsonRPCMessage()   {}

// ParseMessage parses a raw JSON-RPC message represented as a map[string]any into a strongly typed Message (Request, SuccessResponse, or ErrorResponse).
// It returns an error if the message is invalid or does not conform to the JSON-RPC specification.
func ParseMessage(raw map[string]any) (Message, error) {
	jsonrpc, ok := raw["jsonrpc"].(string)
	if !ok || jsonrpc != DEFAULT_JSONRPC_VERSION {
		return nil, NewInvalidJSONRPCFrameError("invalid or missing jsonrpc field")
	}

	_, hasMethod := raw["method"]
	_, hasParams := raw["params"]
	_, hasResult := raw["result"]
	_, hasError := raw["error"]

	if hasParams && !hasMethod {
		return nil, NewInvalidJSONRPCFrameError("params field is only valid for requests")
	}

	if hasMethod {
		if hasResult || hasError {
			return nil, NewInvalidJSONRPCFrameError("request must not include result or error")
		}
		return parseRequest(raw)
	}

	if hasResult && hasError {
		return nil, NewInvalidJSONRPCFrameError("response must not include both result and error")
	}

	if hasResult {
		return parseSuccessResponse(raw)
	}

	if hasError {
		return parseErrorResponse(raw)
	}

	return nil, NewInvalidJSONRPCFrameError("message must be request, success response, or error response")
}

func parseRequest(raw map[string]any) (Request, error) {
	id, ok := raw["id"]
	if !ok || id == nil {
		return Request{}, NewInvalidJSONRPCFrameError("request id is required")
	}
	parsedID, ok := parseID(id)
	if !ok {
		return Request{}, NewInvalidJSONRPCFrameError("request id must be string or number")
	}

	if !isValidNonNullID(parsedID) {
		return Request{}, NewInvalidJSONRPCFrameError("request id must be string or number")
	}

	method, ok := raw["method"].(string)
	if !ok || method == "" {
		return Request{}, NewInvalidJSONRPCFrameError("method must be a non-empty string")
	}

	req := Request{
		JSONRPC: DEFAULT_JSONRPC_VERSION,
		ID:      parsedID,
		Method:  method,
	}

	if params, ok := raw["params"]; ok {
		paramsObj, ok := params.(map[string]any)
		if !ok {
			return Request{}, NewInvalidJSONRPCFrameError("params must be a JSON object")
		}
		req.Params = paramsObj
	}

	return req, nil
}

func parseSuccessResponse(raw map[string]any) (SuccessResponse, error) {
	id, ok := raw["id"]
	if !ok || id == nil {
		return SuccessResponse{}, NewInvalidJSONRPCFrameError("success response id is required")
	}

	parsedID, ok := parseID(id)
	if !ok {
		return SuccessResponse{}, NewInvalidJSONRPCFrameError("success response id must be string or number")
	}

	if !isValidNonNullID(parsedID) {
		return SuccessResponse{}, NewInvalidJSONRPCFrameError("success response id must be string or number")
	}

	result, ok := raw["result"].(map[string]any)
	if !ok {
		return SuccessResponse{}, NewInvalidJSONRPCFrameError("result must be a JSON object")
	}

	return SuccessResponse{
		JSONRPC: DEFAULT_JSONRPC_VERSION,
		ID:      parsedID,
		Result:  result,
	}, nil
}

func parseErrorResponse(raw map[string]any) (ErrorResponse, error) {
	id, hasID := raw["id"]
	if !hasID {
		return ErrorResponse{}, NewInvalidJSONRPCFrameError("error response id field is required, but may be null")
	}

	parsedID, ok := parseID(id)
	if !ok {
		return ErrorResponse{}, NewInvalidJSONRPCFrameError("error response id must be string, number, or null")
	}

	if id != nil && !isValidNonNullID(parsedID) {
		return ErrorResponse{}, NewInvalidJSONRPCFrameError("error response id must be string, number, or null")
	}

	errorRaw, ok := raw["error"].(map[string]any)
	if !ok {
		return ErrorResponse{}, NewInvalidJSONRPCFrameError("error must be a JSON object")
	}

	codeFloat, ok := errorRaw["code"].(float64)
	if !ok || codeFloat != float64(int(codeFloat)) {
		return ErrorResponse{}, NewInvalidJSONRPCFrameError("error.code must be an integer")
	}

	message, ok := errorRaw["message"].(string)
	if !ok || message == "" {
		return ErrorResponse{}, NewInvalidJSONRPCFrameError("error.message must be a non-empty string")
	}

	errObj := ErrorObject{
		Code:    int(codeFloat),
		Message: message,
	}

	if data, ok := errorRaw["data"]; ok && data != nil {
		dataObj, ok := data.(map[string]any)
		if !ok {
			return ErrorResponse{}, NewInvalidJSONRPCFrameError("error.data must be a JSON object when present")
		}
		errObj.Data = dataObj
	}

	return ErrorResponse{
		JSONRPC: DEFAULT_JSONRPC_VERSION,
		ID:      parsedID,
		Error:   errObj,
	}, nil
}

func parseID(id any) (ID, bool) {
	switch v := id.(type) {
	case string:
		return ID{String: &v}, true
	case float64:
		if v != math.Trunc(v) {
			return ID{}, false
		}
		num := int64(v)
		return ID{Number: &num}, true
	default:
		return ID{Null: true}, true
	}
}

func isValidNonNullID(id ID) bool {
	return id.String != nil || id.Number != nil
}
