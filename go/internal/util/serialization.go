package util

import "encoding/json"

// StructToMap converts any struct type into a map[string]any using generics and reflection.
func StructToMap(value any) (map[string]any, error) {
	data, err := json.Marshal(value)
	if err != nil {
		return nil, err
	}

	var out map[string]any
	if err := json.Unmarshal(data, &out); err != nil {
		return nil, err
	}

	return out, nil
}

// MustStructToMap converts any struct type into a map[string]any using generics and reflection.
func MustStructToMap(value any) map[string]any {
	res, err := json.Marshal(value)
	if err != nil {
		panic(err)
	}

	var out map[string]any
	if err := json.Unmarshal(res, &out); err != nil {
		panic(err)
	}

	return out
}
