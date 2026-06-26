package repository

type PrepareRequest struct {
}

type PrepareResult struct {
}

type OpenRequest struct {
}

type SearchRequest struct {
}

type Candidate struct {
}

type Session interface {
	Close() error
}
