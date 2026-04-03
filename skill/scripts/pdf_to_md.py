#!/usr/bin/env python3
"""Convert a PDF file (local or URL) to markdown."""

import sys
import tempfile
import urllib.request
from pathlib import Path

try:
    import pymupdf4llm
except ImportError:
    print("pymupdf4llm not installed. Run: pip3 install pymupdf4llm", file=sys.stderr)
    sys.exit(1)


def convert(source: str, output: str):
    # If source is a URL, download first
    if source.startswith("http://") or source.startswith("https://"):
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            print(f"Downloading {source}...")
            urllib.request.urlretrieve(source, tmp.name)
            pdf_path = tmp.name
    else:
        pdf_path = source

    if not Path(pdf_path).exists():
        print(f"File not found: {pdf_path}", file=sys.stderr)
        sys.exit(1)

    text = pymupdf4llm.to_markdown(pdf_path)

    Path(output).parent.mkdir(parents=True, exist_ok=True)
    Path(output).write_text(text, encoding="utf-8")
    print(f"Saved to {output}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <pdf-path-or-url> <output.md>", file=sys.stderr)
        sys.exit(1)
    convert(sys.argv[1], sys.argv[2])
