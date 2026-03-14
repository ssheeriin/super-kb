"""Helpers for project-scoped Claude Code MCP configuration."""

from __future__ import annotations

import json
from pathlib import Path

DEFAULT_SERVER_NAME = "skb"
DEFAULT_COMMAND = "skb-mcp-server"


def build_project_mcp_config(
    server_name: str = DEFAULT_SERVER_NAME,
    command: str = DEFAULT_COMMAND,
    args: list[str] | None = None,
) -> dict:
    """Build a minimal project-scoped MCP configuration."""
    return {
        "mcpServers": {
            server_name: {
                "command": command,
                "args": args or [],
            }
        }
    }


def inspect_project_mcp_config(project_root: str | Path, server_name: str = DEFAULT_SERVER_NAME) -> dict:
    """Inspect a project's .mcp.json file for an SKB server entry."""
    project_root = Path(project_root).expanduser().resolve()
    mcp_path = project_root / ".mcp.json"
    result = {
        "project_root": str(project_root),
        "path": str(mcp_path),
        "exists": mcp_path.exists(),
        "valid_json": False,
        "has_server": False,
        "server_name": server_name,
        "server_entry": None,
    }

    if not mcp_path.exists():
        return result

    try:
        payload = json.loads(mcp_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        result["error"] = f"Invalid JSON: {exc}"
        return result

    if not isinstance(payload, dict):
        result["error"] = "Top-level JSON value must be an object."
        return result

    mcp_servers = payload.get("mcpServers", {})
    if not isinstance(mcp_servers, dict):
        result["error"] = "The `mcpServers` field must be an object."
        return result

    result["valid_json"] = True
    result["has_server"] = server_name in mcp_servers
    result["server_entry"] = mcp_servers.get(server_name)
    return result


def write_project_mcp_config(
    project_root: str | Path,
    server_name: str = DEFAULT_SERVER_NAME,
    command: str = DEFAULT_COMMAND,
    args: list[str] | None = None,
    force: bool = False,
) -> dict:
    """Create or update a project's .mcp.json with an SKB server entry."""
    project_root = Path(project_root).expanduser().resolve()
    project_root.mkdir(parents=True, exist_ok=True)
    mcp_path = project_root / ".mcp.json"
    desired_entry = {
        "command": command,
        "args": args or [],
    }

    if mcp_path.exists():
        try:
            payload = json.loads(mcp_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            return {
                "path": str(mcp_path),
                "status": "error",
                "error": f"Invalid JSON in existing .mcp.json: {exc}",
            }

        if not isinstance(payload, dict):
            return {
                "path": str(mcp_path),
                "status": "error",
                "error": "Existing .mcp.json must contain a JSON object.",
            }

        mcp_servers = payload.setdefault("mcpServers", {})
        if not isinstance(mcp_servers, dict):
            return {
                "path": str(mcp_path),
                "status": "error",
                "error": "Existing .mcp.json has a non-object `mcpServers` field.",
            }

        existing_entry = mcp_servers.get(server_name)
        if existing_entry == desired_entry:
            return {
                "path": str(mcp_path),
                "status": "unchanged",
                "server_name": server_name,
                "command": command,
                "args": desired_entry["args"],
            }

        if existing_entry is not None and not force:
            return {
                "path": str(mcp_path),
                "status": "skipped",
                "server_name": server_name,
                "error": (
                    f"Existing server entry for {server_name!r} differs. "
                    "Use --force to overwrite it."
                ),
                "existing_entry": existing_entry,
                "desired_entry": desired_entry,
            }

        mcp_servers[server_name] = desired_entry
        status = "updated" if existing_entry is not None else "updated"
    else:
        payload = build_project_mcp_config(server_name=server_name, command=command, args=args)
        status = "created"

    mcp_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return {
        "path": str(mcp_path),
        "status": status,
        "server_name": server_name,
        "command": command,
        "args": desired_entry["args"],
    }
