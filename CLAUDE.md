# CLAUDE.md

Claude Code adapter for this repository.

@./AGENTS.md
@./.claude/CLAUDE-skb.md

## Claude Code Additions

- Prefer the repo skills when the task matches them:
  - `implement-feature`
  - `mcp-tooling`
  - `packaging-release`
  - `clean-room-smoke`
  - `docs-sync`
  - `review-plan`
  - `run-checks`
  - `skb`
- For install, packaging, or release work, keep CLI behavior, release assets,
  installers, uninstallers, tests, and docs aligned.
- When project knowledge or earlier design context matters, search the local
  `.skb/` knowledge base before asking the user to restate existing docs.
