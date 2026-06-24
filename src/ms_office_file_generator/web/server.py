"""``gen-ui`` console-script entry point: launch the web UI with uvicorn.

Binds 127.0.0.1:18990 by default so the UI is not exposed on the network by
accident. Pass ``--host 0.0.0.0`` to expose it (unauthenticated; your choice).
The upload size cap is configurable via ``--max-upload-mb`` or the
``MOFG_MAX_UPLOAD_MB`` environment variable.
"""

from __future__ import annotations

import argparse
import os

import uvicorn

from ms_office_file_generator.web.app import create_app

_DEFAULT_HOST = "127.0.0.1"
_DEFAULT_PORT = 18990
_DEFAULT_MAX_UPLOAD_MB = 25


def _default_max_upload_mb() -> int:
    raw = os.environ.get("MOFG_MAX_UPLOAD_MB")
    if raw is None:
        return _DEFAULT_MAX_UPLOAD_MB
    try:
        value = int(raw)
    except ValueError:
        return _DEFAULT_MAX_UPLOAD_MB
    return value if value > 0 else _DEFAULT_MAX_UPLOAD_MB


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="gen-ui", description="Serve the Office file generator web UI."
    )
    parser.add_argument("--host", default=_DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=_DEFAULT_PORT)
    parser.add_argument(
        "--max-upload-mb",
        type=int,
        default=_default_max_upload_mb(),
        help="Cap for fill-mode uploads (default 25; or MOFG_MAX_UPLOAD_MB).",
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    app = create_app(max_upload_mb=args.max_upload_mb)
    uvicorn.run(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
