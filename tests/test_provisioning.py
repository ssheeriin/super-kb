from pathlib import Path

from skb.provisioning import PROJECT_IMPORT_LINE, provision_project


def test_provision_project_creates_expected_layout(tmp_path: Path) -> None:
    project_dir = tmp_path / "demo-project"
    project_dir.mkdir()

    result = _run_provision(project_dir)

    assert result["project"] == "demo-project"
    assert ".skb" in result["created_directories"]
    assert ".claude/skills/skb" in result["created_directories"]
    assert "CLAUDE.md" in result["created_files"]
    assert (project_dir / ".skb").is_dir()
    assert (project_dir / ".claude" / "CLAUDE-skb.md").is_file()
    assert (project_dir / ".claude" / "skills" / "skb" / "SKILL.md").is_file()
    assert (project_dir / "CLAUDE.md").read_text(encoding="utf-8") == (
        "# Project Instructions\n\n"
        f"{PROJECT_IMPORT_LINE}\n"
    )


def test_provision_project_appends_import_to_existing_claude(tmp_path: Path) -> None:
    project_dir = tmp_path / "existing-claude"
    project_dir.mkdir()
    (project_dir / "CLAUDE.md").write_text("# Existing Instructions\n\n- keep this\n", encoding="utf-8")

    result = _run_provision(project_dir)

    assert "CLAUDE.md" in result["updated_files"]
    content = (project_dir / "CLAUDE.md").read_text(encoding="utf-8")
    assert "# Existing Instructions" in content
    assert PROJECT_IMPORT_LINE in content


def test_provision_project_preserves_modified_generated_files_without_force(tmp_path: Path) -> None:
    project_dir = tmp_path / "modified-files"
    project_dir.mkdir()
    _run_provision(project_dir)

    generated_file = project_dir / ".claude" / "CLAUDE-skb.md"
    generated_file.write_text("# custom skb instructions\n", encoding="utf-8")

    result = _run_provision(project_dir)

    assert generated_file.read_text(encoding="utf-8") == "# custom skb instructions\n"
    assert any(
        item.startswith(".claude/CLAUDE-skb.md (exists; kept existing content)")
        for item in result["skipped_files"]
    )


def test_provision_project_force_overwrites_generated_files(tmp_path: Path) -> None:
    project_dir = tmp_path / "force-overwrite"
    project_dir.mkdir()
    _run_provision(project_dir)

    generated_file = project_dir / ".claude" / "CLAUDE-skb.md"
    generated_file.write_text("# custom skb instructions\n", encoding="utf-8")

    result = _run_provision(project_dir, force=True)

    assert ".claude/CLAUDE-skb.md" in result["updated_files"]
    assert generated_file.read_text(encoding="utf-8") != "# custom skb instructions\n"
    assert "## Super Knowledge Base (.skb/)" in generated_file.read_text(encoding="utf-8")


def _run_provision(project_dir: Path, force: bool = False) -> dict:
    import asyncio

    return asyncio.run(provision_project(project_dir, force=force))
