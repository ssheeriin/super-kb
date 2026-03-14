"""Build a standalone SKB binary bundle and package it for GitHub Releases."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tarfile
import zipfile
from pathlib import Path


APP_NAME = "skb-mcp-server"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--platform-id", required=True, help="Release platform id, for example macos-arm64.")
    parser.add_argument(
        "--output-dir",
        default="release-dist",
        help="Directory where the packaged release archive should be written.",
    )
    args = parser.parse_args(argv)

    repo_root = Path(__file__).resolve().parents[1]
    spec_path = repo_root / "packaging" / "pyinstaller.spec"
    build_root = repo_root / "build" / "pyinstaller" / args.platform_id
    dist_root = repo_root / "dist" / "pyinstaller" / args.platform_id
    output_dir = (repo_root / args.output_dir).resolve()
    bundle_dir = dist_root / APP_NAME

    shutil.rmtree(build_root, ignore_errors=True)
    shutil.rmtree(dist_root, ignore_errors=True)
    output_dir.mkdir(parents=True, exist_ok=True)

    command = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--clean",
        "--noconfirm",
        "--distpath",
        str(dist_root),
        "--workpath",
        str(build_root),
        str(spec_path),
    ]
    subprocess.run(command, check=True, cwd=repo_root)

    if not bundle_dir.exists():
        raise SystemExit(f"Expected PyInstaller bundle at {bundle_dir}")

    archive_path = package_bundle(bundle_dir, output_dir, args.platform_id)
    print(archive_path)
    return 0


def package_bundle(bundle_dir: Path, output_dir: Path, platform_id: str) -> Path:
    """Package a PyInstaller onedir bundle into a release asset archive."""
    if platform_id.startswith("windows-"):
        archive_path = output_dir / f"{APP_NAME}-{platform_id}.zip"
        with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            for path in sorted(bundle_dir.rglob("*")):
                if path.is_file():
                    zf.write(path, arcname=str(Path(APP_NAME) / path.relative_to(bundle_dir)))
        return archive_path

    archive_path = output_dir / f"{APP_NAME}-{platform_id}.tar.gz"
    with tarfile.open(archive_path, "w:gz") as tf:
        tf.add(bundle_dir, arcname=APP_NAME)
    return archive_path


if __name__ == "__main__":
    raise SystemExit(main())
