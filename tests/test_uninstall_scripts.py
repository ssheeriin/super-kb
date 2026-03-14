import os
import stat
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.mark.skipif(os.name == "nt", reason="Shell-script uninstall smoke is POSIX-only")
def test_uninstall_script_removes_installation_and_calls_cleanup(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    home_dir = tmp_path / "home"
    xdg_dir = tmp_path / "xdg"
    install_root = tmp_path / "install-root"
    current_dir = install_root / "current"
    bin_dir = tmp_path / "bin"
    project_dir = tmp_path / "project"
    fake_bin = tmp_path / "fake-bin"
    claude_log = tmp_path / "claude.log"
    exe_log = tmp_path / "exe.log"

    for path in (home_dir, xdg_dir, current_dir, bin_dir, project_dir, fake_bin):
        path.mkdir(parents=True, exist_ok=True)

    executable_path = current_dir / "skb-mcp-server"
    executable_path.write_text(
        "\n".join(
            [
                "#!/usr/bin/env bash",
                "set -eu",
                f"echo \"$@\" >> {exe_log!s}",
                "exit 0",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    executable_path.chmod(executable_path.stat().st_mode | stat.S_IEXEC)

    bin_path = bin_dir / "skb-mcp-server"
    bin_path.symlink_to(executable_path)

    cache_dir = home_dir / ".skb"
    cache_dir.mkdir()
    (cache_dir / "cache.txt").write_text("cached", encoding="utf-8")
    (project_dir / ".mcp.json").write_text('{"mcpServers":{"skb":{"command":"skb-mcp-server","args":[]}}}\n', encoding="utf-8")

    manifest_dir = xdg_dir / "skb-mcp-server"
    manifest_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = manifest_dir / "install-manifest.sh"
    manifest_path.write_text(
        "\n".join(
            [
                f"INSTALL_ROOT={_sh_quote(install_root)}",
                f"CURRENT_DIR={_sh_quote(current_dir)}",
                f"BIN_DIR={_sh_quote(bin_dir)}",
                f"BIN_PATH={_sh_quote(bin_path)}",
                f"EXECUTABLE_PATH={_sh_quote(executable_path)}",
                "CLAUDE_SERVER_NAME='skb'",
                "CLAUDE_REGISTERED='1'",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    claude_path = fake_bin / "claude"
    claude_path.write_text(
        "\n".join(
            [
                "#!/usr/bin/env bash",
                "set -eu",
                f"echo \"$@\" >> {claude_log!s}",
                "if [ \"$1\" = \"mcp\" ] && [ \"$2\" = \"get\" ]; then",
                f"  cat <<'EOF'\nskb:\n  Scope: User config (available in all your projects)\n  Status: ✓ Connected\n  Type: stdio\n  Command: {executable_path}\n  Args:\n  Environment:\nEOF",
                "  exit 0",
                "fi",
                "if [ \"$1\" = \"mcp\" ] && [ \"$2\" = \"remove\" ]; then",
                "  exit 0",
                "fi",
                "exit 1",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    claude_path.chmod(claude_path.stat().st_mode | stat.S_IEXEC)

    env = os.environ.copy()
    env["HOME"] = str(home_dir)
    env["XDG_CONFIG_HOME"] = str(xdg_dir)
    env["PATH"] = f"{fake_bin}:{bin_dir}:{env['PATH']}"

    subprocess.run(
        [
            "bash",
            str(repo_root / "uninstall.sh"),
            "--remove-cache",
            "--remove-project-mcp",
            str(project_dir),
            "--yes",
        ],
        check=True,
        cwd=repo_root,
        env=env,
    )

    assert not current_dir.exists()
    assert not bin_path.exists()
    assert not manifest_path.exists()
    assert not cache_dir.exists()
    assert "mcp remove skb -s user" in claude_log.read_text(encoding="utf-8")
    assert f"remove-mcp-config --project-root {project_dir}" in exe_log.read_text(encoding="utf-8")


def _sh_quote(path: Path) -> str:
    return "'" + str(path).replace("'", "'\"'\"'") + "'"
