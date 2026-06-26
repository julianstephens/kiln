package persistence

import "context"

type Store interface {
	Close() error
	Health(ctx context.Context) error
}
