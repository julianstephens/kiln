import sys

from kiln.repository.server import RepositoryServer


def main() -> int:
    server = RepositoryServer(
        input_stream=sys.stdin.buffer,
        output_stream=sys.stdout.buffer,
    )
    server.serve()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
