"""Command-line interface for SKB."""

from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

from . import PACKAGE_NAME, __version__
from .config import EMBEDDING_MODEL_DIR, RERANK_ENABLED, RERANK_MODEL, SKB_HOME
from .mcp_config import (
    DEFAULT_COMMAND,
    DEFAULT_SERVER_NAME,
    inspect_project_mcp_config,
    remove_project_mcp_config,
    write_project_mcp_config,
)
from .reranker import warm_up as warm_up_reranker
from .server import main as serve_server
from .store import warm_up as warm_up_embeddings


def build_parser() -> argparse.ArgumentParser:
    """Build the top-level CLI parser."""
    parser = argparse.ArgumentParser(
        prog="skb-mcp-server",
        description="Super Knowledge Base (SKB) for Claude Code.",
    )
    subparsers = parser.add_subparsers(dest="command")

    serve_parser = subparsers.add_parser("serve", help="Run the SKB MCP server.")
    serve_parser.set_defaults(handler=_handle_serve)

    version_parser = subparsers.add_parser("version", help="Show the SKB version.")
    version_parser.add_argument("--json", action="store_true", help="Render version info as JSON.")
    version_parser.set_defaults(handler=_handle_version)

    bootstrap_parser = subparsers.add_parser(
        "bootstrap-model",
        help="Download and warm the embedding model ahead of first use.",
    )
    bootstrap_parser.add_argument(
        "--skip-reranker",
        action="store_true",
        help="Do not warm the optional reranker model.",
    )
    bootstrap_parser.add_argument("--json", action="store_true", help="Render bootstrap info as JSON.")
    bootstrap_parser.set_defaults(handler=_handle_bootstrap_model)

    doctor_parser = subparsers.add_parser(
        "doctor",
        help="Inspect the local SKB installation and optional project MCP config.",
    )
    doctor_parser.add_argument(
        "--project-root",
        default=".",
        help="Project root to inspect for .mcp.json and .skb/ (default: current directory).",
    )
    doctor_parser.add_argument("--json", action="store_true", help="Render doctor info as JSON.")
    doctor_parser.set_defaults(handler=_handle_doctor)

    mcp_parser = subparsers.add_parser(
        "write-mcp-config",
        help="Create or update a project-scoped .mcp.json that points Claude Code to SKB.",
    )
    mcp_parser.add_argument(
        "--project-root",
        default=".",
        help="Project root where .mcp.json should be written (default: current directory).",
    )
    mcp_parser.add_argument(
        "--server-name",
        default=DEFAULT_SERVER_NAME,
        help=f"Claude MCP server name (default: {DEFAULT_SERVER_NAME}).",
    )
    mcp_parser.add_argument(
        "--command",
        default=DEFAULT_COMMAND,
        help=f"Executable or absolute path for the SKB server (default: {DEFAULT_COMMAND}).",
    )
    mcp_parser.add_argument(
        "--arg",
        dest="args",
        action="append",
        default=[],
        help="Additional argument to include in the .mcp.json entry. Repeat as needed.",
    )
    mcp_parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite an existing SKB server entry if it differs.",
    )
    mcp_parser.add_argument("--json", action="store_true", help="Render result as JSON.")
    mcp_parser.set_defaults(handler=_handle_write_mcp_config)

    remove_mcp_parser = subparsers.add_parser(
        "remove-mcp-config",
        help="Remove the SKB server entry from a project-scoped .mcp.json.",
    )
    remove_mcp_parser.add_argument(
        "--project-root",
        default=".",
        help="Project root where .mcp.json should be updated (default: current directory).",
    )
    remove_mcp_parser.add_argument(
        "--server-name",
        default=DEFAULT_SERVER_NAME,
        help=f"Claude MCP server name to remove (default: {DEFAULT_SERVER_NAME}).",
    )
    remove_mcp_parser.add_argument(
        "--keep-empty-file",
        action="store_true",
        help="Keep an empty .mcp.json instead of deleting it when the SKB entry was the only content.",
    )
    remove_mcp_parser.add_argument("--json", action="store_true", help="Render result as JSON.")
    remove_mcp_parser.set_defaults(handler=_handle_remove_mcp_config)

    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the SKB CLI."""
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv:
        parser = build_parser()
        if _should_print_help_for_no_args():
            parser.print_help()
            return 0
        return _handle_serve(argparse.Namespace())

    parser = build_parser()
    args = parser.parse_args(argv)
    handler = getattr(args, "handler", None)
    if handler is None:
        parser.print_help()
        return 1
    return handler(args)


def _handle_serve(_args: argparse.Namespace) -> int:
    serve_server()
    return 0


def _should_print_help_for_no_args() -> bool:
    """Treat an attached terminal on stdout/stderr as an interactive invocation."""
    return _stream_isatty(sys.stdout) or _stream_isatty(sys.stderr)


def _stream_isatty(stream: object) -> bool:
    """Check whether a stream is attached to a terminal, including low-level fd probing."""
    isatty = getattr(stream, "isatty", None)
    if callable(isatty):
        try:
            if isatty():
                return True
        except OSError:
            pass

    fileno = getattr(stream, "fileno", None)
    if callable(fileno):
        try:
            return os.isatty(fileno())
        except (AttributeError, OSError, ValueError):
            return False

    return False


def _handle_version(args: argparse.Namespace) -> int:
    payload = {
        "package": PACKAGE_NAME,
        "version": __version__,
        "platform": platform.platform(),
        "python": sys.version.split()[0],
    }
    _emit_result(payload, as_json=args.json)
    return 0


def _handle_bootstrap_model(args: argparse.Namespace) -> int:
    warm_up_embeddings()
    reranker_status = "skipped"
    if not args.skip_reranker:
        warm_up_reranker()
        reranker_status = "warmed" if RERANK_ENABLED else "disabled"

    payload = {
        "status": "ok",
        "model_dir": str(EMBEDDING_MODEL_DIR),
        "model_files_present": [
            str(EMBEDDING_MODEL_DIR / "onnx" / "model.onnx"),
            str(EMBEDDING_MODEL_DIR / "tokenizer.json"),
        ],
        "reranker": {
            "enabled": RERANK_ENABLED,
            "model": RERANK_MODEL,
            "status": reranker_status,
        },
    }
    _emit_result(payload, as_json=args.json)
    return 0


def _handle_doctor(args: argparse.Namespace) -> int:
    payload = run_doctor(project_root=args.project_root)
    _emit_result(payload, as_json=args.json, formatter=_format_doctor_report)
    return 1 if payload["status"] == "error" else 0


def _handle_write_mcp_config(args: argparse.Namespace) -> int:
    payload = write_project_mcp_config(
        project_root=args.project_root,
        server_name=args.server_name,
        command=args.command,
        args=args.args,
        force=args.force,
    )
    exit_code = 0 if payload["status"] in {"created", "updated", "unchanged"} else 1
    _emit_result(payload, as_json=args.json, formatter=_format_write_mcp_config_report)
    return exit_code


def _handle_remove_mcp_config(args: argparse.Namespace) -> int:
    payload = remove_project_mcp_config(
        project_root=args.project_root,
        server_name=args.server_name,
        delete_file_when_empty=not args.keep_empty_file,
    )
    exit_code = 0 if payload["status"] in {"removed", "deleted", "unchanged", "absent"} else 1
    _emit_result(payload, as_json=args.json, formatter=_format_remove_mcp_config_report)
    return exit_code


def run_doctor(project_root: str | Path = ".") -> dict:
    """Inspect the local SKB installation and optional project-scoped config."""
    project_root = Path(project_root).expanduser().resolve()
    project_mcp = inspect_project_mcp_config(project_root)
    claude_path = shutil.which("claude")
    executable_path = shutil.which("skb-mcp-server")
    path_ok = _check_writable_directory(SKB_HOME)
    model_files = [
        EMBEDDING_MODEL_DIR / "onnx" / "model.onnx",
        EMBEDDING_MODEL_DIR / "tokenizer.json",
    ]
    model_cached = all(path.exists() for path in model_files)

    claude_server = _probe_claude_server(claude_path)

    checks = [
        {
            "id": "skb_home_writable",
            "status": "ok" if path_ok else "error",
            "message": f"SKB home directory is {'writable' if path_ok else 'not writable'}: {SKB_HOME}",
        },
        {
            "id": "embedded_model_cached",
            "status": "ok" if model_cached else "warn",
            "message": "Embedding model is cached." if model_cached else "Embedding model is not cached yet.",
        },
        {
            "id": "claude_cli",
            "status": "ok" if claude_path else "warn",
            "message": f"Claude Code CLI found at {claude_path}" if claude_path else "Claude Code CLI not found on PATH.",
        },
        {
            "id": "claude_user_server",
            "status": "ok" if claude_server["configured"] else "warn",
            "message": (
                f"Claude user-scoped MCP server `{DEFAULT_SERVER_NAME}` is configured."
                if claude_server["configured"]
                else f"Claude user-scoped MCP server `{DEFAULT_SERVER_NAME}` is not configured."
            ),
        },
        {
            "id": "project_mcp_json",
            "status": "ok" if project_mcp["has_server"] else "warn",
            "message": (
                f"Project-scoped .mcp.json contains `{DEFAULT_SERVER_NAME}`."
                if project_mcp["has_server"]
                else "Project-scoped .mcp.json does not contain SKB."
            ),
        },
        {
            "id": "project_skb_folder",
            "status": "ok" if (project_root / ".skb").is_dir() else "warn",
            "message": (
                f"Project contains .skb/: {project_root / '.skb'}"
                if (project_root / ".skb").is_dir()
                else f"Project does not contain .skb/: {project_root / '.skb'}"
            ),
        },
    ]

    overall_status = "ok"
    if any(item["status"] == "error" for item in checks):
        overall_status = "error"
    elif any(item["status"] == "warn" for item in checks):
        overall_status = "warn"

    return {
        "status": overall_status,
        "version": __version__,
        "package": PACKAGE_NAME,
        "platform": platform.platform(),
        "python": sys.version.split()[0],
        "executable": executable_path or sys.argv[0],
        "skb_home": str(SKB_HOME),
        "model_dir": str(EMBEDDING_MODEL_DIR),
        "model_cached": model_cached,
        "claude_path": claude_path,
        "claude_server": claude_server,
        "project_root": str(project_root),
        "project_mcp": project_mcp,
        "checks": checks,
    }


def _probe_claude_server(claude_path: str | None) -> dict:
    """Inspect whether the default SKB MCP server is configured in Claude Code."""
    if not claude_path:
        return {
            "available": False,
            "configured": False,
            "output": "",
        }

    try:
        result = subprocess.run(
            [claude_path, "mcp", "get", DEFAULT_SERVER_NAME],
            check=False,
            capture_output=True,
            text=True,
        )
        output = (result.stdout or result.stderr).strip()
        connected = (
            result.returncode == 0
            and "Failed to connect" not in output
            and "Status: ✗" not in output
        )
        return {
            "available": True,
            "configured": connected,
            "output": output,
        }
    except OSError as exc:
        return {
            "available": True,
            "configured": False,
            "output": str(exc),
        }


def _check_writable_directory(path: Path) -> bool:
    """Return True if a directory is writable by creating and removing a temp file."""
    try:
        path.mkdir(parents=True, exist_ok=True)
        probe = path / ".doctor-write-test"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink()
        return True
    except OSError:
        return False


def _emit_result(payload: dict, as_json: bool, formatter=None) -> None:
    """Print structured output in JSON or human-readable form."""
    if as_json:
        print(json.dumps(payload, indent=2, sort_keys=True))
        return
    if formatter is None:
        print(json.dumps(payload, indent=2, sort_keys=True))
        return
    print(formatter(payload))


def _format_doctor_report(payload: dict) -> str:
    """Render `doctor` output as human-readable text."""
    lines = [
        "SKB Doctor",
        f"Status: {payload['status']}",
        f"Version: {payload['version']}",
        f"Executable: {payload['executable']}",
        f"SKB_HOME: {payload['skb_home']}",
        f"Model cache: {'present' if payload['model_cached'] else 'missing'}",
        f"Claude CLI: {payload['claude_path'] or 'not found'}",
        f"Project root: {payload['project_root']}",
    ]
    for check in payload["checks"]:
        lines.append(f"- [{check['status']}] {check['message']}")
    if payload["claude_server"]["output"]:
        lines.append("")
        lines.append("Claude MCP status:")
        lines.append(payload["claude_server"]["output"])
    return "\n".join(lines)


def _format_write_mcp_config_report(payload: dict) -> str:
    """Render `write-mcp-config` output as human-readable text."""
    if payload["status"] == "error":
        return f"Failed to update {payload['path']}: {payload['error']}"
    if payload["status"] == "skipped":
        return f"Skipped {payload['path']}: {payload['error']}"
    return (
        f"{payload['status'].capitalize()} {payload['path']} for server "
        f"{payload['server_name']} -> {payload['command']}"
    )


def _format_remove_mcp_config_report(payload: dict) -> str:
    """Render `remove-mcp-config` output as human-readable text."""
    if payload["status"] == "error":
        return f"Failed to update {payload['path']}: {payload['error']}"
    if payload["status"] == "removed":
        return f"Removed server {payload['server_name']} from {payload['path']}"
    if payload["status"] == "deleted":
        return f"Removed server {payload['server_name']} and deleted empty file {payload['path']}"
    if payload["status"] == "absent":
        return f"No .mcp.json found at {payload['path']}"
    return f"No changes needed in {payload['path']} for server {payload['server_name']}"
