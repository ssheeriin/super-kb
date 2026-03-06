# Claude Code Configuration for SKB

This folder contains the Claude Code configuration files that make SKB work
seamlessly. Copy them to your `~/.claude/` directory.

## Files

```
claude-config/
├── CLAUDE.md              → ~/.claude/CLAUDE.md (append to existing)
└── commands/
    └── skb.md             → ~/.claude/commands/skb.md
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

### 2. Slash command (/skb)

```bash
mkdir -p ~/.claude/commands
cp sample/claude-config/commands/skb.md ~/.claude/commands/skb.md
```

### 3. MCP server registration

Add this to your `~/.claude.json` (create the file if it doesn't exist):

```json
{
  "mcpServers": {
    "skb": {
      "command": "uv",
      "args": ["--directory", "/path/to/super-kb", "run", "server.py"],
      "type": "stdio"
    }
  }
}
```

Replace `/path/to/super-kb` with the actual path where you cloned this repo.

### 4. Restart Claude Code

Restart Claude Code so it picks up the new MCP server and instructions.

## What each file does

| File | Purpose |
|------|---------|
| `CLAUDE.md` | Tells Claude to auto-sync `.skb/` at session start, search the KB before asking for files, and use `search_code` for code examples |
| `commands/skb.md` | Registers the `/skb` slash command with subcommands: `search`, `code`, `sync`, `reindex`, `status`, `docs`, `help` |

## Available commands after setup

| Command | Description |
|---------|-------------|
| `/skb search <query>` | Search knowledge base for docs |
| `/skb code <query>` | Search for code examples |
| `/skb code <query> lang:python` | Search code filtered by language |
| `/skb sync` | Incrementally sync the `.skb/` folder |
| `/skb reindex` | Full reindex of current project |
| `/skb reindex <project>` | Full reindex of a named project |
| `/skb status` | Show all indexed projects |
| `/skb docs` | List indexed files for current project |
| `/skb help` | Show usage |
