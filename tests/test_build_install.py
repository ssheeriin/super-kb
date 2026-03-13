import os
import shutil
import subprocess
import sys
import textwrap
from pathlib import Path


def test_built_wheel_installs_and_provisions_project(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    dist_dir = tmp_path / "dist"
    dist_dir.mkdir()

    subprocess.run(
        [sys.executable, "-m", "build", "--wheel", "--outdir", str(dist_dir)],
        check=True,
        cwd=repo_root,
    )

    wheels = sorted(dist_dir.glob("*.whl"))
    assert len(wheels) == 1
    wheel_path = wheels[0]

    venv_dir = tmp_path / "venv"
    subprocess.run(
        [str(_venv_builder_python()), "-m", "venv", str(venv_dir)],
        check=True,
    )

    python_executable = _venv_python(venv_dir)
    console_script = _venv_script(venv_dir, "skb-mcp-server")

    subprocess.run(
        [str(python_executable), "-m", "pip", "install", str(wheel_path)],
        check=True,
    )

    assert console_script.exists()

    import_check = subprocess.run(
        [
            str(python_executable),
            "-c",
            "from skb.server import main; print(callable(main))",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    assert import_check.stdout.strip() == "True"

    project_dir = tmp_path / "installed-project"
    project_dir.mkdir()
    provision_code = textwrap.dedent(
        f"""
        import asyncio
        from pathlib import Path

        from skb.provisioning import provision_project

        result = asyncio.run(provision_project(Path({str(project_dir)!r})))
        if "error" in result:
            raise SystemExit(result["error"])
        """
    )
    subprocess.run(
        [str(python_executable), "-c", provision_code],
        check=True,
    )

    assert (project_dir / ".skb").is_dir()
    assert (project_dir / ".claude" / "CLAUDE-skb.md").is_file()
    assert (project_dir / ".claude" / "skills" / "skb" / "SKILL.md").is_file()
    assert (project_dir / "CLAUDE.md").is_file()
    assert "## Super Knowledge Base (.skb/)" in (project_dir / ".claude" / "CLAUDE-skb.md").read_text(
        encoding="utf-8"
    )


def _venv_python(venv_dir: Path) -> Path:
    if os.name == "nt":
        return venv_dir / "Scripts" / "python.exe"
    return venv_dir / "bin" / "python"


def _venv_script(venv_dir: Path, name: str) -> Path:
    if os.name == "nt":
        return venv_dir / "Scripts" / f"{name}.exe"
    return venv_dir / "bin" / name


def _venv_builder_python() -> Path:
    python3 = shutil.which("python3")
    if python3:
        return Path(python3)
    return Path(sys.executable)
