import argparse
from pathlib import Path

MIGRATION_DIR = (
    Path(__file__).parent.parent.parent / "go/internal/persistence" / "migrations"
)

TEMPLATE = """
-- +goose up
SELECT 'up SQL query';

-- +goose down
SELECT 'down SQL query';
"""


def create_migration_file(name: str, dry_run: bool = False) -> Path:
    migration_files = sorted(MIGRATION_DIR.glob("*.sql"))
    next_migration_number = 1
    if migration_files:
        last_migration_file = migration_files[-1]
        last_migration_number = int(last_migration_file.stem.split("_")[0])
        next_migration_number = last_migration_number + 1

    sanitized_name = name.replace(" ", "_").replace("-", "_").lower().strip()
    if not sanitized_name:
        raise ValueError("Migration name must not be empty after sanitization")

    migration_filename = f"{next_migration_number:05d}_{sanitized_name}.sql"
    migration_path = MIGRATION_DIR / migration_filename
    if not dry_run:
        migration_path.touch(exist_ok=False)
        migration_path.write_text(TEMPLATE)
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
