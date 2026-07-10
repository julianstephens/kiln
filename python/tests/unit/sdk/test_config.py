from kiln.logger import LoggingConfig, LogSinkConfig
from kiln.sdk.config import RuntimeConfig


def test_dump_args_includes_logging_sink_compress_only_when_true() -> None:
    cfg_with_compress = RuntimeConfig(
        logging=LoggingConfig(
            sink=LogSinkConfig(
                kind="local_file",
                directory="/tmp/logs",
                filename="runtime.log",
                max_bytes=1024,
                max_files=2,
                compress=True,
            )
        )
    )
    cfg_without_compress = RuntimeConfig(
        logging=LoggingConfig(
            sink=LogSinkConfig(
                kind="local_file",
                directory="/tmp/logs",
                filename="runtime.log",
                max_bytes=1024,
                max_files=2,
                compress=False,
            )
        )
    )

    args_with = cfg_with_compress.dump_args()
    args_without = cfg_without_compress.dump_args()

    assert "-logging-sink-compress" in args_with
    assert "-logging-sink-compress" not in args_without


def test_dump_args_omits_logging_format() -> None:
    cfg = RuntimeConfig(
        logging=LoggingConfig(
            format="console",
            sink=LogSinkConfig(kind="stderr"),
        )
    )

    args = cfg.dump_args()

    assert "-logging-format" not in args
