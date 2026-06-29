package contracttests_test

import (
	"encoding/json"
	"os"
	"path/filepath"
	"reflect"
	"runtime"
	"testing"

	"github.com/julianstephens/kiln/go/schema/event/envelope"
	searchrequestpayload "github.com/julianstephens/kiln/go/schema/repository/search_request_payload"
)

func fixturePath(t *testing.T, name string) string {
	t.Helper()

	_, filename, _, ok := runtime.Caller(0)
	if !ok {
		t.Fatal("could not determine test file path")
	}

	return filepath.Join(
		filepath.Dir(filename),
		"..",
		"..",
		"contract-fixtures",
		"v1",
		name,
	)
}

func readFixture(t *testing.T, name string) []byte {
	t.Helper()

	data, err := os.ReadFile(fixturePath(t, name))
	if err != nil {
		t.Fatalf("read fixture %s: %v", name, err)
	}

	return data
}

func decodeJSONDocument(t *testing.T, data []byte) map[string]any {
	t.Helper()

	var document map[string]any
	if err := json.Unmarshal(data, &document); err != nil {
		t.Fatalf("decode JSON document: %v", err)
	}

	return document
}

func assertJSONRoundTrip[T interface{ Validate() error }](t *testing.T, fixtureName string) {
	t.Helper()

	data := readFixture(t, fixtureName)

	var value T
	if err := json.Unmarshal(data, &value); err != nil {
		t.Fatalf("unmarshal %s: %v", fixtureName, err)
	}

	if err := value.Validate(); err != nil {
		t.Fatalf("validate %s: %v", fixtureName, err)
	}

	serialized, err := json.Marshal(value)
	if err != nil {
		t.Fatalf("serialize %s: %v", fixtureName, err)
	}

	expected := decodeJSONDocument(t, data)
	actual := decodeJSONDocument(t, serialized)

	if !reflect.DeepEqual(actual, expected) {
		t.Fatalf("round-trip mismatch for %s\nexpected: %#v\nactual:   %#v", fixtureName, expected, actual)
	}
}

func TestContractFixtureValidatesAndSerializes(t *testing.T) {
	t.Run("event envelope", func(t *testing.T) {
		assertJSONRoundTrip[envelope.Envelope](t, "event-envelope.valid.json")
	})

	t.Run("repository search request payload", func(t *testing.T) {
		assertJSONRoundTrip[searchrequestpayload.SearchRequestPayload](
			t,
			"repository-search-request-payload.valid.json",
		)
	})
}

func TestInvalidContractFixtureFailsGoValidation(t *testing.T) {
	data := readFixture(t, "repository-search-request-payload.invalid.missing-query.json")

	var value searchrequestpayload.SearchRequestPayload
	if err := json.Unmarshal(data, &value); err != nil {
		t.Fatalf("unmarshal invalid fixture: %v", err)
	}

	if err := value.Validate(); err == nil {
		t.Fatal("expected missing query fixture to fail validation")
	}
}
