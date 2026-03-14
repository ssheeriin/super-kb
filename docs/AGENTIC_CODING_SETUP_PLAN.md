# Agentic Coding Setup

## Goal

Enable this repository to work well with:

- Claude Code
- Codex
- Cline

without maintaining three unrelated sets of project instructions or skill bodies.

## Research Summary

### Claude Code

- Claude Code uses a project `CLAUDE.md` file for repository-specific memory and
  instructions.
- Claude-specific reusable workflows can live in `.claude/skills/`.

### Codex

- Codex supports repository `AGENTS.md` files as the primary project instruction
  format.
- This repository uses `.codex/skills/` as the generated project skill target.

### Cline

- Cline's primary project rule format is `.clinerules/`.
- Cline also recognizes `AGENTS.md`, which makes it useful as a shared baseline.
- Cline can use project skill directories; this repository uses `.cline/skills/`.

## Implemented Layout

```text
AGENTS.md
CLAUDE.md
.claude/
  CLAUDE-skb.md
  skills/
.clinerules/
.codex/
  skills/
.cline/
  skills/
agent-skills/
  skills.toml
  <skill-name>/
    body.md
scripts/
  sync_agent_skills.py
```

## Design Principles

1. Keep one shared source for the portable skill bodies.
2. Keep one shared rule file for cross-tool project instructions.
3. Use tool-specific files only where the tool needs a distinct adapter.
4. Avoid hardcoded references to unrelated local repositories or local filesystem
   paths in markdown, templates, or generated skills.

## Skill Set

The shared source currently defines:

- `implement-feature`
- `mcp-tooling`
- `packaging-release`
- `clean-room-smoke`
- `docs-sync`
- `review-plan`
- `run-checks`
- `skb`

## Sync Model

`scripts/sync_agent_skills.py` reads `agent-skills/skills.toml` and generates:

- `.claude/skills/`
- `.codex/skills/`
- `.cline/skills/`

Tool-specific frontmatter overrides are applied from the manifest, so the skill
body stays shared.

## Maintenance Rules

- Edit `agent-skills/` first, not the generated targets.
- Re-run `python3 scripts/sync_agent_skills.py` after changing the skill source.
- Keep `AGENTS.md`, `CLAUDE.md`, and `.clinerules/` short and stable.
- Keep runtime docs in `README.md` and `USERGUIDE.md` aligned when the user flow
  changes.

## Next Recommended Step

If you want a deeper Cline integration later, add:

- `memory-bank/`
- `.clineignore`

Those are intentionally not part of this initial baseline.
