# Java Project Example

This sample shows the project-scoped Claude Code setup for a Java repository.

Files:

- `.mcp.json`
  Check this into the repo if you want the project itself to declare that it
  uses SKB.

Recommended team workflow:

1. Each developer installs `skb-mcp-server` once with `install.sh` or
   `install.ps1`.
2. The Java repo commits `.mcp.json`.
3. Developers open Claude Code in the repo.
4. Claude can use SKB in that project without each developer manually running
   a project-specific `claude mcp add ...` command.
