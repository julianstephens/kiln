from dataclasses import Field, dataclass, field, fields, is_dataclass
from pathlib import Path
from typing import Any, Literal

from kiln.logger import LoggingConfig

DEFAULT_KILN_DIR = Path.home() / ".kiln"

CLI = "cli"


def _kebab(name: str) -> str:
    return name.replace("_", "-")


def _cli_meta(dc_field: Field) -> dict[str, str]:
    return dc_field.metadata.get(CLI, {})


def _map_value(value: Any, meta: dict[str, Any]) -> Any:
    value_map = meta.get("map")
    if isinstance(value_map, dict):
        return value_map.get(value, value)
    return value


def _iter_cli_args(obj: Any, path: tuple[str, ...] = ()):
    if is_dataclass(obj):
        for f in fields(obj):
            meta = _cli_meta(f)
            if not meta.get("emit", True):
                continue

            raw = getattr(obj, f.name)
            name = meta.get("name", _kebab(f.name))
            next_path = (*path, name)

            if is_dataclass(raw):
                yield from _iter_cli_args(raw, next_path)
                continue

            if raw is None:
                continue

            flag = "-" + "-".join(next_path)
            value = _map_value(raw, meta)

            # bool flags are switch-style for flagsfiller: include only when true
            if isinstance(value, bool):
                if value:
                    yield (flag,)
                continue

            yield (flag, str(value))
        return


@dataclass(frozen=True)
class ShutdownConfig:
    process_exit_timeout_seconds: int = 30
    kill_timeout_seconds: int = 10
    cancel_in_flight_requests: bool = True


@dataclass(frozen=True)
class DBConfig:
    db_type: Literal["sqlite3", "turso"] = "sqlite3"
    installation_db_path: str = ":memory:"
    max_open_connections: int = 10
    max_idle_connections: int = 5
    max_connection_lifetime_seconds: int = 3600


@dataclass(frozen=True)
class RuntimeConfig:
    logging: LoggingConfig = field(
        default_factory=LoggingConfig,
        metadata={CLI: {"name": "logging"}},
    )
    db: DBConfig = field(
        default_factory=DBConfig,
        metadata={CLI: {"name": "db"}},
    )

    def dump_args(self) -> tuple[str, ...]:
        args: list[str] = []
        for item in _iter_cli_args(self):
            if len(item) == 1:
                args.append(item[0])
            else:
                args.extend([item[0], item[1]])
        return tuple(args)
