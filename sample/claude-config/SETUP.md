# Claude Code Configuration for SKB

This folder contains the Claude Code configuration files that make SKB work
seamlessly. Copy them to your `~/.claude/` directory.

## Files

```
claude-config/
├── CLAUDE.md              → ~/.claude/CLAUDE.md (append to existing)
└── skills/
    └── skb/
        └── SKILL.md       → ~/.claude/skills/skb/SKILL.md
```

## Installation

### 1. Global instructions (CLAUDE.md)

If you already have a `~/.claude/CLAUDE.md`, **append** the contents:

```bash
cat sample/claude-config/CLAUDE.md >> ~/.claude/CLAUDE.md
```

If you don't have one yet:

```bash
cp sample/claude-config/CLAUDE.md ~/.claude/CLAUDE.md
```

### 2. Install the `skb` skill

```bash
mkdir -p ~/.claude/skills/skb
cp sample/claude-config/skills/skb/SKILL.md ~/.claude/skills/skb/SKILL.md
```

### 3. MCP server registration

Register SKB with Claude Code using the MCP CLI:

```bash
claude mcp add skb --scope user -- uv --directory /path/to/super-kb run python -m skb
```

Replace `/path/to/super-kb` with the actual path where you cloned this repo.
Use `--scope user` so the server is available in every project on your machine.

Verify the registration:

```bash
claude mcp get skb
```

### 4. Restart Claude Code

Restart Claude Code so it picks up the new MCP server and instructions.

## What each file does

| File | Purpose |
|------|---------|
| `CLAUDE.md` | Tells Claude to auto-sync `.skb/` at session start, search the KB before asking for files, and use `search_code` for code examples |
| `skills/skb/SKILL.md` | Registers the `skb` skill, which you can invoke with `/skb` for provisioning, search, sync, reindex, export, and import workflows |

## Available commands after setup

| Command | Description |
|---------|-------------|
| `/skb provision` | Provision SKB into the current project |
| `/skb search <query>` | Search knowledge base for docs |
| `/skb code <query>` | Search for code examples |
| `/skb code <query> lang:python` | Search code filtered by language |
| `/skb sync` | Incrementally sync the `.skb/` folder |
| `/skb reindex` | Full reindex of current project |
| `/skb reindex <project>` | Full reindex of a named project |
| `/skb status` | Show all indexed projects |
| `/skb docs` | List indexed files for current project |
| `/skb export` | Export both source files and vector index |
| `/skb export-source <path>` | Export only the `.skb/` source files |
| `/skb export-index <path>` | Export only the vector index |
| `/skb import <source_path> <index_path>` | Import both source files and vector index |
| `/skb import-source <path> [--replace]` | Import `.skb/` source files, then sync |
| `/skb import-index <path>` | Import only the vector index |
| `/skb help` | Show usage |
