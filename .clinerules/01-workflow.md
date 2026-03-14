# Cline Workflow

- Follow `AGENTS.md` as the canonical project rule file.
- Use plan-first workflow for multi-file runtime, packaging, installer, or
  release changes.
- Keep generated skill content sourced from `agent-skills/`; do not manually edit
  `.claude/skills/`, `.codex/skills/`, or `.cline/skills/` unless you are also
  updating the shared source and re-syncing.
- Treat `.skb/` as user-managed project context and do not reorganize or remove
  it unless the user asks.
