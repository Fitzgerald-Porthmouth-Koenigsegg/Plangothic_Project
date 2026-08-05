#!/usr/bin/env python3
"""Insert or replace the generated Plangothic download table in release notes."""

from __future__ import annotations

import argparse
from pathlib import Path
import re

START_MARKER = "<!-- plangothic-downloads:start -->"
END_MARKER = "<!-- plangothic-downloads:end -->"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--current-body", type=Path, required=True)
    parser.add_argument("--block-file", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    current = args.current_body.read_text(encoding="utf-8").strip()
    block = args.block_file.read_text(encoding="utf-8").strip()

    if START_MARKER not in block or END_MARKER not in block:
        raise ValueError("The generated download block is missing its marker comments")

    pattern = re.compile(
        re.escape(START_MARKER) + r".*?" + re.escape(END_MARKER),
        flags=re.DOTALL,
    )

    if pattern.search(current):
        updated = pattern.sub(block, current)
    elif current:
        updated = f"{current}\n\n{block}"
    else:
        updated = block

    args.output.write_text(updated.rstrip() + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
