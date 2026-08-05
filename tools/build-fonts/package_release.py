#!/usr/bin/env python3
"""Create Plangothic release archives from the generated build branch."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import re
import shutil
import subprocess
from urllib.parse import quote

PACKAGE_DIRS = {
    "OTF": "otf",
    "Static": "static",
    "Web": "web",
}

START_MARKER = "<!-- plangothic-downloads:start -->"
END_MARKER = "<!-- plangothic-downloads:end -->"


def safe_component(value: str, label: str) -> str:
    value = value.strip()
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._+-]*", value):
        raise ValueError(
            f"Invalid {label}: {value!r}; use letters, digits, dot, underscore, plus, or hyphen"
        )
    return value


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def require_nonempty_directory(path: Path) -> None:
    if not path.is_dir() or not any(item.is_file() for item in path.rglob("*")):
        raise FileNotFoundError(f"Missing or empty font directory: {path}")


def create_archives(dist_dir: Path, package_dir: Path) -> list[Path]:
    archive_base = dist_dir / package_dir.name
    zip_path = Path(
        shutil.make_archive(
            str(archive_base),
            "zip",
            root_dir=dist_dir,
            base_dir=package_dir.name,
        )
    )
    seven_zip_path = Path(f"{archive_base}.7z")
    subprocess.run(
        ["7z", "a", "-t7z", "-mx=9", str(seven_zip_path), package_dir.name],
        cwd=dist_dir,
        check=True,
    )
    return [seven_zip_path, zip_path]


def write_download_links(
    dist_dir: Path,
    repository: str,
    font_name: str,
    version: str,
) -> None:
    base_url = f"https://github.com/{repository}/releases/download/{quote(version, safe='')}"
    lines = [
        START_MARKER,
        "### 下载链接 / Downloads",
        "",
        "| Package | 7z | zip |",
        "| --- | --- | --- |",
    ]

    for package_name in ("Super", "Static", "OTF", "Web"):
        base = f"{font_name}-{package_name}-{version}"
        seven_zip = quote(f"{base}.7z", safe="")
        zip_name = quote(f"{base}.zip", safe="")
        lines.append(
            f"| {package_name} | [📦 Download]({base_url}/{seven_zip}) | "
            f"[📦 Download]({base_url}/{zip_name}) |"
        )

    lines.extend([END_MARKER, ""])
    (dist_dir / "download-links.md").write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fonts-dir", type=Path, required=True)
    parser.add_argument("--dist-dir", type=Path, required=True)
    parser.add_argument("--font-name", required=True)
    parser.add_argument("--version", required=True)
    parser.add_argument("--repository", required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    fonts_dir = args.fonts_dir.resolve()
    dist_dir = args.dist_dir.resolve()
    font_name = safe_component(args.font_name, "font name")
    version = safe_component(args.version, "version")

    for subdirectory in PACKAGE_DIRS.values():
        require_nonempty_directory(fonts_dir / subdirectory)

    shutil.rmtree(dist_dir, ignore_errors=True)
    dist_dir.mkdir(parents=True)

    release_files: list[Path] = []
    for package_name, subdirectory in PACKAGE_DIRS.items():
        package_dir = dist_dir / f"{font_name}-{package_name}-{version}"
        shutil.copytree(fonts_dir / subdirectory, package_dir)
        release_files.extend(create_archives(dist_dir, package_dir))

    super_dir = dist_dir / f"{font_name}-Super-{version}"
    super_dir.mkdir()
    for subdirectory in PACKAGE_DIRS.values():
        shutil.copytree(fonts_dir / subdirectory, super_dir / subdirectory)
    release_files.extend(create_archives(dist_dir, super_dir))

    static_dir = dist_dir / f"{font_name}-Static-{version}"
    release_files.extend(sorted(static_dir.glob("*.ttf")))

    checksum_lines = [f"{sha256(path)}  {path.relative_to(dist_dir).as_posix()}" for path in release_files]
    (dist_dir / "SHA256SUMS.txt").write_text("\n".join(sorted(checksum_lines)) + "\n", encoding="utf-8")

    write_download_links(dist_dir, args.repository, font_name, version)

    print("Created release assets:")
    for path in sorted(release_files):
        print(f"- {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
