import gzip
import logging
import os
import shutil
import sys
from dataclasses import dataclass, field
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Literal, TextIO

import structlog

from .errors import (
    LoggerError,
    UnsupportedLogFormatError,
    UnsupportedLogLevelError,
    UnsupportedLogSinkKindError,
)

LogSinkKind = Literal["stderr", "local_file"]
LogLevel = Literal["debug", "info", "warning", "error", "critical"]
LogFormat = Literal["json", "console"]


@dataclass(frozen=True)
class LogSinkConfig:
    kind: LogSinkKind = "stderr"

    directory: str | None = None
    filename: str | None = None

    max_bytes: int | None = None
    max_files: int | None = None
    compress: bool = False


@dataclass(frozen=True)
class LoggingConfig:
    level: LogLevel = field(
        default="info",
        metadata={"cli": {"map": {"warning": "warn", "critical": "error"}}},
    )
    format: LogFormat = field(default="json", metadata={"cli": {"emit": False}})
    sink: LogSinkConfig = field(default_factory=LogSinkConfig)


class GzipRotatingFileHandler(RotatingFileHandler):
    def rotation_filename(self, default_name: str) -> str:
        return f"{default_name}.gz"

    def rotate(self, source: str, dest: str) -> None:
        with open(source, "rb") as src, gzip.open(dest, "wb") as dst:
            shutil.copyfileobj(src, dst)
        os.remove(source)


def configure_logging(
    config: LoggingConfig,
    *,
    fallback: TextIO = sys.stderr,
) -> None:
    handler = _make_handler(config.sink, fallback=fallback)
    handler.setLevel(_level(config.level))
    handler.setFormatter(logging.Formatter("%(message)s"))

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(_level(config.level))

    processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    if config.format == "console":
        processors.append(structlog.dev.ConsoleRenderer())
    elif config.format == "json":
        processors.append(structlog.processors.JSONRenderer())
    else:
        raise UnsupportedLogFormatError(config.format)

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def _make_handler(
    sink: LogSinkConfig,
    *,
    fallback: TextIO,
) -> logging.Handler:
    if sink.kind == "stderr":
        return logging.StreamHandler(fallback)

    if sink.kind == "local_file":
        return _make_local_file_handler(sink)

    raise UnsupportedLogSinkKindError(sink.kind)


def _make_local_file_handler(sink: LogSinkConfig) -> logging.Handler:
    if not sink.directory:
        raise LoggerError(message="local file log sink requires directory")
    if not sink.filename:
        raise LoggerError(message="local file log sink requires filename")
    if Path(sink.filename).name != sink.filename:
        raise LoggerError(
            message="local file log sink filename must not include path separators"
        )
    if sink.max_bytes is None or sink.max_bytes <= 0:
        raise LoggerError(
            message="local file log sink requires max_bytes greater than zero"
        )
    if sink.max_files is None or sink.max_files <= 0:
        raise LoggerError(
            message="local file log sink requires max_files greater than zero"
        )

    directory = Path(sink.directory)
    directory.mkdir(mode=0o700, parents=True, exist_ok=True)

    path = directory / sink.filename
    handler_cls = GzipRotatingFileHandler if sink.compress else RotatingFileHandler

    return handler_cls(
        filename=path,
        maxBytes=sink.max_bytes,
        backupCount=sink.max_files,
        encoding="utf-8",
    )


def _level(level: LogLevel) -> int:
    match level:
        case "debug":
            return logging.DEBUG
        case "info":
            return logging.INFO
        case "warning":
            return logging.WARNING
        case "error":
            return logging.ERROR
        case "critical":
            return logging.CRITICAL
        case _:
            raise UnsupportedLogLevelError(level)
