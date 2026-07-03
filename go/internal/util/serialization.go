package util

import (
	"reflect"
)

// StructToMap converts any struct type into a map[string]any using generics and reflection.
func StructToMap[T any](obj T) map[string]any {
	result := make(map[string]any)
	val := reflect.ValueOf(obj)

	// Handle pointer to struct if passed
	if val.Kind() == reflect.Pointer {
		val = val.Elem()
	}

	// Ensure we are operating on a struct
	if val.Kind() != reflect.Struct {
		return result
	}

	t := val.Type()
	for i := 0; i < val.NumField(); i++ {
		field := t.Field(i)
		fieldVal := val.Field(i)

		// Skip unexported fields
		if !fieldVal.CanInterface() {
			continue
		}

		// Use JSON tag as key if available, otherwise use field name
		key := field.Name
		if tag := field.Tag.Get("json"); tag != "" && tag != "-" {
			key = tag
		}

		result[key] = fieldVal.Interface()
	}

	return result
}
