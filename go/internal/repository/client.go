package repository

import "context"

type Client interface {
	Prepare(ctx context.Context, request PrepareRequest) (PrepareResult, error)
	Open(ctx context.Context, request OpenRequest) (Session, error)
	Search(ctx context.Context, session Session, request SearchRequest) ([]Candidate, error)
	Close(ctx context.Context, session Session) error
}
