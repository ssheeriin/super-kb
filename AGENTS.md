# AGENTS.md

This file is the canonical cross-tool instruction set for coding agents in this
repository. Tool-specific files such as `CLAUDE.md` or `.clinerules/` should add
only tool-specific behavior and point back to this file for the core rules.

## Project Summary

- `super-kb` is a Python MCP server and CLI for a local project knowledge base
  backed by embeddings and vector search.
- The runtime package lives in `skb/`.
- The project ships installers, uninstallers, release automation, provisioning
  templates, and standalone binary packaging.
- The main workflows are MCP server behavior, CLI behavior, packaging, release
  automation, and clean-room install verification.

## Core Commands

```bash
uv run --with pytest pytest -q
uv run --with pytest --with build pytest -q
python3 -m py_compile skb/*.py skb/chunkers/*.py tests/*.py scripts/*.py
python3 scripts/sync_agent_skills.py
uv run python -m skb version
```

## Repository Map

- `skb/` runtime package
- `skb/server.py` MCP server entrypoint
- `skb/cli.py` CLI entrypoint and multi-command frontend
- `skb/tools.py` MCP tool registration
- `skb/provisioning.py` project bootstrap and local Claude setup generation
- `skb/mcp_config.py` project-scoped MCP config helpers
- `skb/templates/` packaged runtime templates
- `tests/` unit and integration coverage
- `scripts/` release and packaging helpers
- `packaging/` PyInstaller spec and packaging support
- `.github/workflows/` CI and release automation
- `sample/claude-config/` reference config for consumers

## Architecture Rules

- Keep runtime logic inside `skb/`.
- Keep packaged templates under `skb/templates/` and keep sample files aligned
  with the runtime templates when both are intended to represent the same flow.
- Prefer explicit subcommands and explicit MCP wiring over ambiguous runtime
  behavior.
- Treat installers, uninstallers, release workflow, and docs as part of the
  product surface, not as secondary artifacts.

## Implementation Standards

- Preserve clean separation between:
  - CLI behavior
  - MCP server behavior
  - provisioning and project config generation
  - packaging and release automation
- When adding or changing an MCP tool, update:
  - runtime implementation
  - tests
  - user-facing docs if behavior changed
- When changing install or release behavior, keep these aligned:
  - `install.sh`
  - `install.ps1`
  - `uninstall.sh`
  - `uninstall.ps1`
  - `.github/workflows/release.yml`
  - `README.md`
  - `USERGUIDE.md`
- Keep generated or bundled paths portable. Do not hardcode unrelated local repo
  paths into documentation, templates, or skill content.

## Testing Expectations

- Run targeted tests first for the changed area.
- For behavior that affects packaging, install, CLI entrypoints, or release
  assets, prefer the broader validation command:
  `uv run --with pytest --with build pytest -q`
- Run `py_compile` for Python-only scaffolding or generator scripts.
- If a clean-room or packaged-binary flow is affected, say whether it was
  exercised or not.

## Working Style

- Read adjacent tests before changing runtime behavior.
- Do not overwrite or revert unrelated user changes already present in the
  worktree.
- Keep docs concise and task-oriented.
- Favor root-cause fixes over compatibility hacks where possible.

## Documentation Targets

- `README.md` for install and first-use flow
- `USERGUIDE.md` for operational and architectural details
- `CHANGELOG.md` for release-facing changes
- `sample/claude-config/` for end-user Claude setup examples

## Tooling Notes

- `CLAUDE.md` is the Claude Code adapter for this repo.
- `.clinerules/` contains Cline-specific rules.
- `agent-skills/` is the shared source-of-truth for portable skills.
- `scripts/sync_agent_skills.py` generates the tool-specific skill directories:
  - `.claude/skills/`
  - `.codex/skills/`
  - `.cline/skills/`
