from __future__ import annotations

import argparse
import itertools
from pathlib import Path
from typing import Iterable

from alter.core.downloader import TaskConfig
from alter.core.models import DownloadRequest
from alter.ui.app import DownloadApp


def _build_requests(urls: list[str], outputs: list[str] | None) -> Iterable[DownloadRequest]:
    outputs_list = outputs or []
    for url, output in itertools.zip_longest(urls, outputs_list, fillvalue=None):
        output_path = Path(output) if output else None
        yield DownloadRequest(url=url, output=output_path)


def main() -> None:
    parser = argparse.ArgumentParser(description="Alter download manager")
    parser.add_argument("url", nargs="*", help="URL(s) to download")
    parser.add_argument("-o", "--output", nargs="*", help="Output path(s)")
    parser.add_argument("--parts", type=int, default=6, help="Number of parts for multipart downloads")
    parser.add_argument("--chunk-size", type=int, default=1024 * 1024, help="Chunk size in bytes")
    parser.add_argument("--timeout", type=int, default=30, help="Request timeout in seconds")
    parser.add_argument("--connections", type=int, default=4, help="Max concurrent connections per download")
    args = parser.parse_args()

    requests = list(_build_requests(args.url, args.output))
    config = TaskConfig(
        parts=args.parts,
        chunk_size=args.chunk_size,
        timeout=args.timeout,
        max_connections=args.connections,
    )

    app = DownloadApp(requests, config=config)
    app.run()


if __name__ == "__main__":
    main()
