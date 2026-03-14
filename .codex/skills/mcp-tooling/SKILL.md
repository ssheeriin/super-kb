---
name: "mcp-tooling"
description: "Add or change MCP tools, provisioning behavior, CLI mappings, and project MCP config flows in super-kb."
---

# MCP Tooling

Use this skill for work on MCP tools, provisioning, server wiring, project-scoped
MCP config generation, and CLI-to-MCP mapping behavior.

## Primary Code Areas

- `skb/server.py`
- `skb/tools.py`
- `skb/provisioning.py`
- `skb/mcp_config.py`
- `skb/cli.py`
- `tests/test_provisioning.py`
- `tests/test_build_install.py`

## Workflow

1. Trace the current user flow first:
   - installed command
   - MCP registration or `.mcp.json`
   - tool invocation
   - provisioned project files
2. Keep the CLI, MCP tool registration, and docs aligned.
3. When behavior affects a provisioned project, update both packaged templates and
   sample config if applicable.

## Output

- Call out whether the change affects user-scoped setup, project-scoped setup, or
  both.
- Include the exact user-facing command or tool flow that changed.
