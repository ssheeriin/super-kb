import json
from pathlib import Path

from skb import cli
from skb.mcp_config import inspect_project_mcp_config, remove_project_mcp_config, write_project_mcp_config


def test_write_project_mcp_config_creates_file(tmp_path: Path) -> None:
    result = write_project_mcp_config(tmp_path)

    assert result["status"] == "created"
    mcp_path = tmp_path / ".mcp.json"
    assert mcp_path.is_file()
    payload = json.loads(mcp_path.read_text(encoding="utf-8"))
    assert payload == {
        "mcpServers": {
            "skb": {
                "command": "skb-mcp-server",
                "args": [],
            }
        }
    }


def test_write_project_mcp_config_requires_force_for_different_entry(tmp_path: Path) -> None:
    mcp_path = tmp_path / ".mcp.json"
    mcp_path.write_text(
        json.dumps(
            {
                "mcpServers": {
                    "skb": {
                        "command": "/custom/skb-mcp-server",
                        "args": ["serve"],
                    }
                }
            }
        ),
        encoding="utf-8",
    )

    skipped = write_project_mcp_config(tmp_path, command="skb-mcp-server")
    assert skipped["status"] == "skipped"

    updated = write_project_mcp_config(tmp_path, command="skb-mcp-server", force=True)
    assert updated["status"] == "updated"
    payload = json.loads(mcp_path.read_text(encoding="utf-8"))
    assert payload["mcpServers"]["skb"] == {
        "command": "skb-mcp-server",
        "args": [],
    }


def test_run_doctor_reports_project_mcp_and_model_cache(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(cli, "SKB_HOME", tmp_path / "skb-home")
    monkeypatch.setattr(cli, "EMBEDDING_MODEL_DIR", tmp_path / "skb-home" / "models" / "bge-small-en-v1.5")
    monkeypatch.setattr(cli, "_check_writable_directory", lambda _path: True)
    monkeypatch.setattr(cli.platform, "platform", lambda: "test-platform")
    monkeypatch.setattr(cli.shutil, "which", lambda name: f"/usr/bin/{name}" if name in {"claude", "skb-mcp-server"} else None)
    monkeypatch.setattr(
        cli,
        "_probe_claude_server",
        lambda _path: {
            "available": True,
            "configured": True,
            "output": "skb: connected",
        },
    )

    model_dir = cli.EMBEDDING_MODEL_DIR
    (model_dir / "onnx").mkdir(parents=True)
    (model_dir / "onnx" / "model.onnx").write_text("x", encoding="utf-8")
    (model_dir / "tokenizer.json").write_text("{}", encoding="utf-8")
    write_project_mcp_config(tmp_path)
    (tmp_path / ".skb").mkdir()

    result = cli.run_doctor(tmp_path)

    assert result["status"] == "ok"
    assert result["model_cached"] is True
    assert result["project_mcp"]["has_server"] is True
    assert result["claude_server"]["configured"] is True
    assert inspect_project_mcp_config(tmp_path)["has_server"] is True


def test_remove_project_mcp_config_deletes_empty_file(tmp_path: Path) -> None:
    write_project_mcp_config(tmp_path)

    result = remove_project_mcp_config(tmp_path)

    assert result["status"] == "deleted"
    assert not (tmp_path / ".mcp.json").exists()


def test_remove_project_mcp_config_preserves_other_servers(tmp_path: Path) -> None:
    mcp_path = tmp_path / ".mcp.json"
    mcp_path.write_text(
        json.dumps(
            {
                "mcpServers": {
                    "skb": {
                        "command": "skb-mcp-server",
                        "args": [],
                    },
                    "other": {
                        "command": "other-server",
                        "args": ["serve"],
                    },
                }
            }
        ),
        encoding="utf-8",
    )

    result = remove_project_mcp_config(tmp_path)

    assert result["status"] == "removed"
    payload = json.loads(mcp_path.read_text(encoding="utf-8"))
    assert payload == {
        "mcpServers": {
            "other": {
                "command": "other-server",
                "args": ["serve"],
            }
        }
    }


def test_remove_project_mcp_config_returns_unchanged_when_absent(tmp_path: Path) -> None:
    result = remove_project_mcp_config(tmp_path)

    assert result["status"] == "absent"


def test_main_without_args_prints_help_for_interactive_terminal(capsys, monkeypatch) -> None:
    monkeypatch.setattr(cli.sys.stdin, "isatty", lambda: True)
    monkeypatch.setattr(cli.sys.stdout, "isatty", lambda: True)
    monkeypatch.setattr(cli, "_handle_serve", lambda _args: (_ for _ in ()).throw(AssertionError("serve should not run")))

    exit_code = cli.main([])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "usage: skb-mcp-server" in captured.out


def test_main_without_args_starts_server_for_non_interactive_stdio(monkeypatch) -> None:
    monkeypatch.setattr(cli.sys.stdin, "isatty", lambda: False)
    monkeypatch.setattr(cli.sys.stdout, "isatty", lambda: False)
    monkeypatch.setattr(cli, "_handle_serve", lambda _args: 0)

    assert cli.main([]) == 0
