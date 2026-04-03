#!/usr/bin/env python3
"""Extract main content from a URL and save as markdown."""

import sys
from pathlib import Path

try:
    import trafilatura
except ImportError:
    print("trafilatura not installed. Run: pip3 install trafilatura", file=sys.stderr)
    sys.exit(1)


def clip(url: str, output: str):
    downloaded = trafilatura.fetch_url(url)
    if not downloaded:
        print(f"Failed to fetch: {url}", file=sys.stderr)
        sys.exit(1)

    text = trafilatura.extract(
        downloaded,
        include_links=True,
        include_images=True,
        include_tables=True,
        output_format="markdown",
    )
    if not text:
        print(f"Failed to extract content from: {url}", file=sys.stderr)
        sys.exit(1)

    Path(output).parent.mkdir(parents=True, exist_ok=True)
    Path(output).write_text(text, encoding="utf-8")
    print(f"Saved to {output}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <url> <output.md>", file=sys.stderr)
        sys.exit(1)
    clip(sys.argv[1], sys.argv[2])
