"""Project-local provisioning for SKB."""

import asyncio
from collections.abc import Callable
from importlib.resources import files
from pathlib import Path

from .config import SKB_FOLDER

PROJECT_IMPORT_LINE = "@./.claude/CLAUDE-skb.md"
PROJECT_CLAUDE_HEADER = "# Project Instructions"


def _template_text(*relative_parts: str) -> str:
    """Load a bundled SKB provisioning template."""
    template_path = files("skb").joinpath("templates", "claude-config", *relative_parts)
    return template_path.read_text(encoding="utf-8")


def _relative_to_project(path: Path, project_dir: Path) -> str:
    """Return a project-relative path string."""
    return str(path.relative_to(project_dir))


async def _maybe_log(log_callback: Callable | None, message: str) -> None:
    """Log a provisioning message if a callback is available."""
    if log_callback:
        await log_callback(message)
        await asyncio.sleep(0)


def _read_text(path: Path) -> str:
    """Read UTF-8 text from disk."""
    return path.read_text(encoding="utf-8")


def _write_text(path: Path, content: str) -> None:
    """Write UTF-8 text to disk."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


async def _ensure_directory(
    path: Path,
    project_dir: Path,
    created_directories: list[str],
    log_callback: Callable | None,
) -> None:
    """Create a directory if it does not already exist."""
    if not path.is_dir():
        path.mkdir(parents=True, exist_ok=True)
        created_directories.append(_relative_to_project(path, project_dir))
        await _maybe_log(log_callback, f"Created {path}")


async def _ensure_file_from_template(
    target_path: Path,
    template_content: str,
    project_dir: Path,
    created_files: list[str],
    updated_files: list[str],
    skipped_files: list[str],
    log_callback: Callable | None,
    force: bool,
) -> None:
    """Create or update a generated file from a template."""
    relative_path = _relative_to_project(target_path, project_dir)

    if not target_path.exists():
        _write_text(target_path, template_content)
        created_files.append(relative_path)
        await _maybe_log(log_callback, f"Created {target_path}")
        return

    current_content = _read_text(target_path)
    if current_content == template_content:
        skipped_files.append(f"{relative_path} (already matches template)")
        return

    if force:
        _write_text(target_path, template_content)
        updated_files.append(relative_path)
        await _maybe_log(log_callback, f"Updated {target_path}")
        return

    skipped_files.append(f"{relative_path} (exists; kept existing content)")


async def provision_project(
    project_dir: str | Path,
    force: bool = False,
    log_callback: Callable | None = None,
) -> dict:
    """Provision SKB into a project directory.

    Creates a local `.skb/` folder, installs the project-local `skb` skill,
    writes a reusable SKB-specific Claude instructions file, and wires the
    project's `CLAUDE.md` to import those instructions.
    """
    project_dir = Path(project_dir).expanduser().resolve()
    if not project_dir.exists() or not project_dir.is_dir():
        return {"error": f"Project directory does not exist: {project_dir}"}

    try:
        template_claude = _template_text("CLAUDE.md")
        template_skill = _template_text("skills", "skb", "SKILL.md")
    except FileNotFoundError as exc:
        return {
            "project": project_dir.name,
            "project_dir": str(project_dir),
            "error": "Missing SKB provisioning templates",
            "missing_templates": [str(exc)],
        }

    created_directories: list[str] = []
    created_files: list[str] = []
    updated_files: list[str] = []
    skipped_files: list[str] = []

    project_skb_dir = project_dir / SKB_FOLDER
    project_claude_dir = project_dir / ".claude"
    project_skill_dir = project_claude_dir / "skills" / "skb"
    project_skb_claude = project_claude_dir / "CLAUDE-skb.md"
    project_claude = project_dir / "CLAUDE.md"

    await _ensure_directory(project_skb_dir, project_dir, created_directories, log_callback)
    await _ensure_directory(project_skill_dir, project_dir, created_directories, log_callback)

    await _ensure_file_from_template(
        project_skb_claude,
        template_claude,
        project_dir,
        created_files,
        updated_files,
        skipped_files,
        log_callback,
        force,
    )
    await _ensure_file_from_template(
        project_skill_dir / "SKILL.md",
        template_skill,
        project_dir,
        created_files,
        updated_files,
        skipped_files,
        log_callback,
        force,
    )

    claude_relative_path = _relative_to_project(project_claude, project_dir)
    if project_claude.exists():
        claude_content = _read_text(project_claude)
        if PROJECT_IMPORT_LINE in claude_content:
            skipped_files.append(f"{claude_relative_path} (SKB import already present)")
        elif "mcp__skb__sync_skb" in claude_content or "## Super Knowledge Base (.skb/)" in claude_content:
            skipped_files.append(f"{claude_relative_path} (SKB instructions already present)")
        else:
            updated_content = claude_content.rstrip() + f"\n\n{PROJECT_IMPORT_LINE}\n"
            _write_text(project_claude, updated_content)
            updated_files.append(claude_relative_path)
            await _maybe_log(log_callback, f"Updated {project_claude}")
    else:
        _write_text(project_claude, f"{PROJECT_CLAUDE_HEADER}\n\n{PROJECT_IMPORT_LINE}\n")
        created_files.append(claude_relative_path)
        await _maybe_log(log_callback, f"Created {project_claude}")

    return {
        "project": project_dir.name,
        "project_dir": str(project_dir),
        "force": force,
        "created_directories": created_directories,
        "created_files": created_files,
        "updated_files": updated_files,
        "skipped_files": skipped_files,
        "next_steps": [
            f"Add project documents to {SKB_FOLDER}/",
            "Restart Claude Code or open a new session to load the local skill and project CLAUDE.md",
            "Run sync_skb after adding files to .skb/",
        ],
    }
