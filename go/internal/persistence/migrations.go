package persistence

import (
	"context"
	"database/sql"
	"embed"
	"io/fs"
	"strconv"
	"strings"

	"github.com/pressly/goose/v3"
)

//go:embed migrations/*.sql
var migrations embed.FS

func migrate(ctx context.Context, db *sql.DB) error {
	migrationFS, err := fs.Sub(migrations, "migrations")
	if err != nil {
		return err
	}
	provider, err := goose.NewProvider(
		goose.DialectSQLite3,
		db,
		migrationFS,
	)
	if err != nil {
		return err
	}

	_, err = provider.Up(ctx)

	return err
}

func currentDBVersion(ctx context.Context, db *sql.DB) (int64, error) {
	migrationFS, err := fs.Sub(migrations, "migrations")
	if err != nil {
		return 0, err
	}
	provider, err := goose.NewProvider(
		goose.DialectSQLite3,
		db,
		migrationFS,
	)
	if err != nil {
		return 0, err
	}

	version, err := provider.GetDBVersion(ctx)
	if err != nil {
		return 0, err
	}

	return version, nil
}

func latestEmbeddedMigrationVersion() (int64, error) {
	entries, err := migrations.ReadDir("migrations")
	if err != nil {
		return 0, err
	}

	var latestVersion int64 = 0
	for _, entry := range entries {
		if !entry.IsDir() && strings.HasSuffix(entry.Name(), ".sql") {
			migrationNo := strings.Split(entry.Name(), "_")[0]
			parsedVersion, err := strconv.ParseInt(migrationNo, 10, 64)
			if err != nil {
				return 0, err
			}
			if parsedVersion > latestVersion {
				latestVersion = parsedVersion
			}
		}
	}
	return latestVersion, nil
}
