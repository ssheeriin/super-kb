"""Sync shared agent skill sources into tool-specific skill directories."""

from __future__ import annotations

import argparse
import json
import shutil
import tomllib
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = REPO_ROOT / "agent-skills"
MANIFEST_PATH = SOURCE_ROOT / "skills.toml"
TARGET_ROOTS = {
    "claude": REPO_ROOT / ".claude" / "skills",
    "codex": REPO_ROOT / ".codex" / "skills",
    "cline": REPO_ROOT / ".cline" / "skills",
}
IGNORED_SOURCE_NAMES = {"body.md"}


def load_manifest() -> dict:
    with MANIFEST_PATH.open("rb") as handle:
        return tomllib.load(handle)


def render_frontmatter(skill_name: str, description: str, overrides: dict | None = None) -> str:
    payload = {"name": skill_name, "description": description}
    if overrides:
        payload.update(overrides)

    lines = ["---"]
    for key, value in payload.items():
        lines.extend(render_yaml_field(key, value))
    lines.append("---")
    return "\n".join(lines)


def render_yaml_field(key: str, value: object) -> list[str]:
    if isinstance(value, bool):
        return [f"{key}: {'true' if value else 'false'}"]
    if isinstance(value, (int, float)):
        return [f"{key}: {value}"]
    if isinstance(value, str):
        return [f"{key}: {json.dumps(value)}"]
    if isinstance(value, list):
        lines = [f"{key}:"]
        for item in value:
            if isinstance(item, str):
                lines.append(f"  - {json.dumps(item)}")
            elif isinstance(item, bool):
                lines.append(f"  - {'true' if item else 'false'}")
            else:
                lines.append(f"  - {item}")
        return lines
    raise TypeError(f"Unsupported frontmatter value for {key}: {type(value)!r}")


def sync_target(tool_name: str, manifest: dict) -> None:
    target_root = TARGET_ROOTS[tool_name]
    target_root.mkdir(parents=True, exist_ok=True)

    for skill_name, skill_config in sorted(manifest["skills"].items()):
        skill_source_dir = SOURCE_ROOT / skill_name
        skill_target_dir = target_root / skill_name

        if skill_target_dir.exists():
            shutil.rmtree(skill_target_dir)
        skill_target_dir.mkdir(parents=True)

        body_path = SOURCE_ROOT / skill_config["body"]
        body = body_path.read_text(encoding="utf-8").rstrip() + "\n"
        overrides = skill_config.get("target_overrides", {}).get(tool_name, {})
        frontmatter = render_frontmatter(skill_name, skill_config["description"], overrides)
        target_skill_path = skill_target_dir / "SKILL.md"
        target_skill_path.write_text(f"{frontmatter}\n\n{body}", encoding="utf-8")

        if not skill_source_dir.exists():
            continue

        for source_path in sorted(skill_source_dir.iterdir()):
            if source_path.name in IGNORED_SOURCE_NAMES:
                continue
            destination = skill_target_dir / source_path.name
            if source_path.is_dir():
                shutil.copytree(source_path, destination)
            else:
                shutil.copy2(source_path, destination)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--target",
        action="append",
        choices=sorted(TARGET_ROOTS),
        help="Specific target skill directory to generate. Defaults to all targets.",
    )
    args = parser.parse_args(argv)

    manifest = load_manifest()
    targets = args.target or list(TARGET_ROOTS)
    for target in targets:
        sync_target(target, manifest)
        print(f"synced {target} -> {TARGET_ROOTS[target]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
