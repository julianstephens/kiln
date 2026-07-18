import argparse
import re
from pathlib import Path

MIGRATION_DIR = (
    Path(__file__).parent.parent.parent / "go/internal/persistence" / "migrations"
)

TEMPLATE = """-- +goose Up
SELECT 'up SQL query';

-- +goose Down
SELECT 'down SQL query';
"""

MIGRATION_FILENAME_RE = re.compile(r"^(?P<number>\d{5})_(?P<name>[a-z0-9_]+)\.sql$")
MIGRATION_FILENAME_FORMAT = "00001_migration_name.sql"


def _next_migration_number() -> int:
    max_migration_number = 0
    for migration_file in sorted(MIGRATION_DIR.glob("*.sql")):
        match = MIGRATION_FILENAME_RE.match(migration_file.name)
        if not match:
            raise ValueError(
                "Malformed migration filename "
                f"'{migration_file.name}'. Expected format: {MIGRATION_FILENAME_FORMAT}"
            )

        migration_number = int(match.group("number"))
        max_migration_number = max(max_migration_number, migration_number)

    return max_migration_number + 1


def create_migration_file(name: str, dry_run: bool = False) -> Path:
    next_migration_number = _next_migration_number()

    sanitized_name = name.replace(" ", "_").replace("-", "_").lower().strip()
    if not sanitized_name:
        raise ValueError("Migration name must not be empty after sanitization")

    migration_filename = f"{next_migration_number:05d}_{sanitized_name}.sql"
    migration_path = MIGRATION_DIR / migration_filename
    if not dry_run:
        with migration_path.open("x", encoding="utf-8") as migration_file:
            migration_file.write(TEMPLATE)
    return migration_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a new Kiln DB migration")

    parser.add_argument("name", help="Name of the new migration")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Perform a dry run without creating the migration file",
    )

    return parser.parse_args()


def main() -> int:
    args = parse_args()

    try:
        migration_path = create_migration_file(args.name, dry_run=args.dry_run)
        if args.dry_run:
            print(
                f"dry run: would create migration for name '{args.name}' at {migration_path!s}"
            )
        else:
            print(f"created new migration: {migration_path!s}")
    except Exception as e:
        print(f"failed to create migration: {e!s}")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
