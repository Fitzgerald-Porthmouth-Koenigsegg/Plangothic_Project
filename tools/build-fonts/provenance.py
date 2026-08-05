#!/usr/bin/env python3
"""Compute a stable fingerprint for every file that affects font build output."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

BUILD_INPUT_PATHS = (
    "sources/Plangothic-Regular.7z",
    "tools/optimize_glyph.py",
    "tools/convert_font.py",
    "tools/build-fonts/build_fonts.py",
    "tools/build-fonts/requirements.txt",
    ".github/workflows/build-fonts.yml",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def compute_input_provenance(repo_root: Path) -> dict[str, object]:
    repo_root = repo_root.resolve()
    entries: list[dict[str, object]] = []

    for relative in BUILD_INPUT_PATHS:
        path = repo_root / relative
        if not path.is_file():
            raise FileNotFoundError(f"Missing build input: {path}")
        entries.append(
            {
                "path": relative,
                "size": path.stat().st_size,
                "sha256": sha256(path),
            }
        )

    fingerprint = hashlib.sha256()
    for entry in entries:
        fingerprint.update(str(entry["path"]).encode("utf-8"))
        fingerprint.update(b"\0")
        fingerprint.update(str(entry["sha256"]).encode("ascii"))
        fingerprint.update(b"\n")

    return {
        "fingerprint": fingerprint.hexdigest(),
        "files": entries,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--json", action="store_true", help="Print the complete provenance object")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    provenance = compute_input_provenance(args.repo_root)
    if args.json:
        print(json.dumps(provenance, ensure_ascii=False, indent=2))
    else:
        print(provenance["fingerprint"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
