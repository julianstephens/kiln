package model

import "context"

type Adapter interface {
	CountTokens(ctx context.Context, request Request) (TokenCount, error)
	Complete(ctx context.Context, request Request) (Response, error)
}
