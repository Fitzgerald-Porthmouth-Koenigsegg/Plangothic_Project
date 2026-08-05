#!/usr/bin/env python3
"""Build Plangothic static, OpenType, web-font, and collection outputs."""

from __future__ import annotations

import argparse
import concurrent.futures
import datetime as dt
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Iterable, Sequence

from fontTools.ttLib import TTCollection, TTFont

from provenance import compute_input_provenance

EXPECTED_STEMS = ("PlangothicP1-Regular", "PlangothicP2-Regular")


def log(message: str) -> None:
    print(message, flush=True)


def run(command: Sequence[str], *, cwd: Path | None = None, capture: bool = False) -> str:
    log("+ " + " ".join(str(part) for part in command))
    result = subprocess.run(
        [str(part) for part in command],
        cwd=cwd,
        check=True,
        text=True,
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.STDOUT if capture else None,
    )
    return result.stdout.strip() if capture and result.stdout else ""


def run_parallel(commands: Iterable[Sequence[str]], jobs: int) -> None:
    command_list = list(commands)
    if not command_list:
        return

    workers = max(1, min(jobs, len(command_list)))
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
        futures = [executor.submit(run, command) for command in command_list]
        for future in concurrent.futures.as_completed(futures):
            future.result()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def discover_sources(input_dir: Path) -> list[Path]:
    discovered: dict[str, Path] = {}
    for path in sorted(input_dir.rglob("Plangothic*-Regular.ttf")):
        if path.stem in discovered:
            raise RuntimeError(f"Duplicate source font stem {path.stem}: {discovered[path.stem]} and {path}")
        discovered[path.stem] = path

    missing = [stem for stem in EXPECTED_STEMS if stem not in discovered]
    if missing:
        available = ", ".join(sorted(discovered)) or "none"
        raise FileNotFoundError(f"Missing source fonts: {', '.join(missing)}; discovered: {available}")

    extras = sorted(set(discovered) - set(EXPECTED_STEMS))
    if extras:
        log(f"Ignoring additional matching fonts: {', '.join(extras)}")

    return [discovered[stem] for stem in EXPECTED_STEMS]


def optimize_fonts(
    sources: list[Path],
    optimized_dir: Path,
    optimize_script: Path,
    simplify: float,
    jobs: int,
) -> list[Path]:
    optimized_dir.mkdir(parents=True, exist_ok=True)

    commands = [
        ["fontforge", "-script", str(optimize_script), str(source), "-s", str(simplify)]
        for source in sources
    ]
    run_parallel(commands, jobs)

    outputs: list[Path] = []
    for source in sources:
        generated = source.with_name(f"{source.stem}_merge_glyphs{source.suffix}")
        if not generated.is_file() or generated.stat().st_size == 0:
            raise RuntimeError(f"FontForge did not create the expected optimized font: {generated}")

        destination = optimized_dir / generated.name
        shutil.move(str(generated), destination)
        outputs.append(destination)

    return outputs


def convert_fonts(
    optimized_fonts: list[Path],
    output_dir: Path,
    convert_script: Path,
    jobs: int,
) -> dict[str, list[Path]]:
    static_dir = output_dir / "static"
    otf_dir = output_dir / "otf"
    web_dir = output_dir / "web"
    for directory in (static_dir, otf_dir, web_dir):
        directory.mkdir(parents=True, exist_ok=True)

    results: dict[str, list[Path]] = {"static": [], "otf": [], "web": []}
    conversion_commands: list[list[str]] = []

    for optimized in optimized_fonts:
        suffix = "_merge_glyphs"
        if not optimized.stem.endswith(suffix):
            raise ValueError(f"Unexpected optimized font name: {optimized.name}")

        base = optimized.stem[: -len(suffix)]
        static_output = static_dir / f"{base}.ttf"
        otf_output = otf_dir / f"{base}.otf"
        web_output = web_dir / f"{base}.woff2"

        shutil.copy2(optimized, static_output)
        results["static"].append(static_output)
        results["otf"].append(otf_output)
        results["web"].append(web_output)

        conversion_commands.extend(
            [
                [
                    "fontforge",
                    "-script",
                    str(convert_script),
                    str(optimized),
                    "--output",
                    str(otf_output),
                    "--format",
                    "otf",
                ],
                [
                    "fontforge",
                    "-script",
                    str(convert_script),
                    str(optimized),
                    "--output",
                    str(web_output),
                    "--format",
                    "woff2",
                ],
            ]
        )

    run_parallel(conversion_commands, jobs)

    for path in results["otf"] + results["web"]:
        if not path.is_file() or path.stat().st_size == 0:
            raise RuntimeError(f"FontForge did not create the expected converted font: {path}")

    return results


def create_collection(input_files: list[Path], output_file: Path) -> None:
    collection = TTCollection()
    collection.fonts = [TTFont(str(path), recalcBBoxes=False, recalcTimestamp=False) for path in input_files]
    try:
        collection.save(str(output_file))
    finally:
        for font in collection.fonts:
            font.close()

    log(f"Created collection: {output_file}")


def validate_single_font(path: Path) -> None:
    if not path.is_file() or path.stat().st_size == 0:
        raise RuntimeError(f"Missing or empty font: {path}")
    font = TTFont(str(path), lazy=True)
    font.close()


def validate_collection(path: Path, expected_count: int) -> None:
    if not path.is_file() or path.stat().st_size == 0:
        raise RuntimeError(f"Missing or empty collection: {path}")
    collection = TTCollection(str(path), lazy=True)
    try:
        if len(collection.fonts) != expected_count:
            raise RuntimeError(
                f"Collection {path} contains {len(collection.fonts)} fonts; expected {expected_count}"
            )
    finally:
        for font in collection.fonts:
            font.close()


def git_output(repo_root: Path, *arguments: str) -> str:
    try:
        return run(["git", *arguments], cwd=repo_root, capture=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        return ""



def display_path(path: Path, repo_root: Path) -> str:
    try:
        return path.relative_to(repo_root).as_posix()
    except ValueError:
        return path.as_posix()


def package_version(name: str) -> str:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return "unknown"


def write_build_info(
    repo_root: Path,
    output_dir: Path,
    build_info_dir: Path,
    source_archive: Path,
) -> None:
    build_info_dir.mkdir(parents=True, exist_ok=True)

    fontforge_version = "unknown"
    try:
        fontforge_version = run(["fontforge", "-version"], capture=True).splitlines()[0]
    except (subprocess.CalledProcessError, FileNotFoundError, IndexError):
        pass

    commit_sha = os.environ.get("GITHUB_SHA") or git_output(repo_root, "rev-parse", "HEAD")
    commit_message = git_output(repo_root, "log", "-1", "--pretty=%B")
    source_ref = os.environ.get("GITHUB_REF_NAME") or git_output(
        repo_root, "branch", "--show-current"
    )

    files = []
    for path in sorted(output_dir.rglob("*")):
        if not path.is_file():
            continue
        files.append(
            {
                "path": display_path(path, repo_root),
                "size": path.stat().st_size,
                "sha256": sha256(path),
            }
        )

    input_provenance = compute_input_provenance(repo_root)

    info = {
        "schema_version": 2,
        "built_at": dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z"),
        "source": {
            "commit_sha": commit_sha,
            "ref": source_ref,
            "commit_message": commit_message,
            "archive": display_path(source_archive, repo_root),
            "archive_sha256": sha256(source_archive),
            "input_fingerprint": input_provenance["fingerprint"],
            "inputs": input_provenance["files"],
        },
        "workflow": {
            "run_id": os.environ.get("GITHUB_RUN_ID", ""),
            "run_number": os.environ.get("GITHUB_RUN_NUMBER", ""),
            "actor": os.environ.get("GITHUB_ACTOR", ""),
            "repository": os.environ.get("GITHUB_REPOSITORY", ""),
        },
        "toolchain": {
            "python": sys.version.split()[0],
            "fontforge": fontforge_version,
            "fonttools": package_version("fonttools"),
            "brotli": package_version("Brotli"),
        },
        "files": files,
    }

    (build_info_dir / "build-info.json").write_text(
        json.dumps(info, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    manifest = [
        "# Build artifact manifest",
        "",
        f"- Source commit: `{commit_sha}`",
        f"- Source archive SHA-256: `{info['source']['archive_sha256']}`",
        f"- Build input fingerprint: `{info['source']['input_fingerprint']}`",
        "",
        "| File | Size (bytes) | SHA-256 |",
        "| --- | ---: | --- |",
    ]
    manifest.extend(
        f"| `{entry['path']}` | {entry['size']} | `{entry['sha256']}` |" for entry in files
    )
    (build_info_dir / "manifest.md").write_text("\n".join(manifest) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    repo_root = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, default=repo_root / "build")
    parser.add_argument("--optimized-dir", type=Path, default=repo_root / "optimized")
    parser.add_argument("--output-dir", type=Path, default=repo_root / "fonts")
    parser.add_argument("--build-info-dir", type=Path, default=repo_root / "build-info")
    parser.add_argument(
        "--source-archive",
        type=Path,
        default=repo_root / "sources" / "Plangothic-Regular.7z",
    )
    parser.add_argument("--jobs", type=int, default=max(1, os.cpu_count() or 1))
    parser.add_argument("--simplify", type=float, default=0.5)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = Path(__file__).resolve().parents[2]

    input_dir = args.input_dir.resolve()
    optimized_dir = args.optimized_dir.resolve()
    output_dir = args.output_dir.resolve()
    build_info_dir = args.build_info_dir.resolve()
    source_archive = args.source_archive.resolve()
    optimize_script = repo_root / "tools" / "optimize_glyph.py"
    convert_script = repo_root / "tools" / "convert_font.py"

    for required in (input_dir, source_archive, optimize_script, convert_script):
        if not required.exists():
            raise FileNotFoundError(required)

    shutil.rmtree(optimized_dir, ignore_errors=True)
    shutil.rmtree(output_dir, ignore_errors=True)
    shutil.rmtree(build_info_dir, ignore_errors=True)

    sources = discover_sources(input_dir)
    log("Source fonts: " + ", ".join(str(path) for path in sources))

    optimized = optimize_fonts(
        sources,
        optimized_dir,
        optimize_script,
        args.simplify,
        args.jobs,
    )
    outputs = convert_fonts(optimized, output_dir, convert_script, args.jobs)

    static_collection = output_dir / "static" / "Plangothic.ttc"
    otf_collection = output_dir / "otf" / "Plangothic.ttc"
    create_collection(outputs["static"], static_collection)
    create_collection(outputs["otf"], otf_collection)

    for path in outputs["static"] + outputs["otf"] + outputs["web"]:
        validate_single_font(path)
    validate_collection(static_collection, len(EXPECTED_STEMS))
    validate_collection(otf_collection, len(EXPECTED_STEMS))

    write_build_info(repo_root, output_dir, build_info_dir, source_archive)
    log("Build completed successfully.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise
