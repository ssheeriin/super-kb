# SKB — Super Knowledge Base for Claude Code

A local MCP server that turns `.skb/` folders in your projects into a searchable vector knowledge base. Drop files in, and Claude Code can find them automatically — no `@` mentions needed.

## Quick Start

```bash
# 1. Create a .skb/ folder in any project
mkdir my-project/.skb

# 2. Drop in your context files
cp design-doc.md my-project/.skb/
cp api-spec.pdf my-project/.skb/
cp auth-example.py my-project/.skb/

# 3. Start Claude Code in that project
cd my-project && claude

# 4. Claude automatically syncs and searches your docs
```

## How It Works

```
my-project/
├── .skb/                    ← Drop files here
│   ├── architecture.md
│   ├── api-reference.pdf
│   └── snippets/
│       └── retry-logic.py
├── src/
└── ...

         ↓ auto-indexed

    ChromaDB (local)          ← Vectors stored in ~/.skb/chromadb/
         ↓
    MCP Server (stdio)        ← Claude Code calls tools over JSON-RPC
         ↓
    Claude Code               ← Searches your docs instead of asking you
```

The MCP server watches each project's `.skb/` folder. When you sync, it:
- Chunks documents by type (markdown by headers, code by functions, etc.)
- Embeds them using BAAI/bge-small-en-v1.5 (custom ONNX, local — no API key needed)
- Reranks search results with FlashRank cross-encoder for better relevance
- Stores metadata (source file, project, section, timestamps)
- Skips unchanged files on re-sync

## Supported File Types

| Type | Extensions | Chunking Strategy |
|------|-----------|-------------------|
| Markdown | `.md` | Split on `##`/`###` headers |
| Plain text | `.txt`, `.rst` | Paragraph boundaries |
| PDF | `.pdf` | Page extraction via pypdf |
| Code | `.py`, `.js`, `.ts`, `.java`, `.go`, `.rs` | Function/class boundaries |
| Config | `.yaml`, `.yml`, `.json` | Whole file (typically small) |

## MCP Tools

The server exposes 7 tools to Claude Code:

| Tool | Description |
|------|-------------|
| `sync_skb` | Scan `.skb/` and ingest/update files. Incremental — only processes changes. |
| `search_docs` | Semantic search across project documentation. |
| `search_code` | Search filtered to code files only, with optional language filter. |
| `list_projects` | Show all indexed projects with chunk counts. |
| `list_documents` | List indexed files for a project with metadata. |
| `remove_project` | Delete all indexed data for a project. |
| `reindex_project` | Force a full reindex: delete all data and rebuild from scratch. |

## Slash Command

Use `/skb` in Claude Code for quick access:

```
/skb search <query>           # Search the knowledge base
/skb code <query>             # Search for code examples
/skb sync                     # Re-sync after adding files
/skb reindex                  # Full reindex of current project
/skb status                   # Show indexed projects
/skb docs                     # List indexed files
/skb help                     # Show usage
```

## Cross-Project Search

By default, searches are scoped to the current project. To search across all indexed projects:

```
> "Search all my projects for how we handle retry logic"
```

Claude will call `search_docs` with `search_all_projects=true`.

## Adding Files Mid-Session

```bash
# In another terminal:
cp new-doc.md my-project/.skb/

# Back in Claude Code:
> "I added new-doc.md to .skb, please sync"
```

## Installation

### Prerequisites

- [uv](https://docs.astral.sh/uv/) package manager
- Python 3.12 or 3.13

### Step 1: Clone the Repository

```bash
git clone https://github.com/ssheeriin/super-kb.git
```

Dependencies install automatically on first run via `uv run`. No manual install step needed.

### Step 2: Claude Code Configuration

Three configurations are needed to set up SKB in Claude Code:

#### 2a. MCP Server Registration (`~/.claude.json`)

Add the SKB server entry under `"mcpServers"` in your `~/.claude.json` (create the file if it doesn't exist):

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

Replace `/path/to/super-kb` with the actual path where you cloned the repository.

#### 2b. Global Instructions (`~/.claude/CLAUDE.md`)

This tells Claude to automatically sync and search your knowledge base at session start. Append the contents of `sample/claude-config/CLAUDE.md` to your global instructions:

```bash
# Append to existing CLAUDE.md
cat sample/claude-config/CLAUDE.md >> ~/.claude/CLAUDE.md

# Or copy if you don't have one yet
cp sample/claude-config/CLAUDE.md ~/.claude/CLAUDE.md
```

Without this, you'd have to manually ask Claude to sync/search every time.

#### 2c. Slash Command (`~/.claude/commands/skb.md`)

This registers the `/skb` slash command for quick access:

```bash
mkdir -p ~/.claude/commands
cp sample/claude-config/commands/skb.md ~/.claude/commands/skb.md
```

### Step 3: Restart Claude Code

Restart Claude Code so it picks up the new MCP server and instructions.

## What Goes in `.skb/`

**Good candidates:**
- Architecture and design documents
- API references and specifications
- Setup and onboarding notes
- Code snippets and patterns for reference
- Configuration examples
- Meeting notes with technical decisions

**Don't put in `.skb/`:**
- Binary files or images
- `node_modules` or build artifacts
- Secrets or credentials
- Very large files (>1MB) — chunk quality degrades

## Git

Add `.skb/` to `.gitignore` if the docs are personal. Commit it if you want to share project context with your team.

## Project Structure

```
super-kb/
├── pyproject.toml           # Dependencies: mcp, chromadb, pypdf, flashrank
├── server.py                # MCP entry point (FastMCP)
├── skb/
│   ├── config.py            # Constants and extension maps
│   ├── store.py             # ChromaDB wrapper
│   ├── embeddings.py        # Custom ONNX embedding function (bge-small-en-v1.5)
│   ├── reranker.py          # FlashRank cross-encoder reranker
│   ├── ingest.py            # File → chunks → vectors pipeline
│   ├── sync.py              # .skb/ folder scanner, incremental sync
│   ├── tools.py             # MCP tool implementations
│   └── chunkers/
│       ├── markdown.py      # Header-aware splitting
│       ├── code.py          # Function/class boundary splitting
│       ├── text.py          # Paragraph-based splitting
│       └── pdf.py           # pypdf extraction + splitting
└── logs/
```

## Technology Stack

All components are open source and permissively licensed.

| Component | Package | License |
|-----------|---------|---------|
| MCP SDK | `mcp` (FastMCP) | MIT |
| Vector store | ChromaDB | Apache 2.0 |
| Embeddings | BAAI/bge-small-en-v1.5 (custom ONNX) | MIT |
| Reranker | FlashRank (`flashrank`) | Apache 2.0 |
| PDF parsing | pypdf | BSD-3-Clause |
| Package manager | uv | Apache 2.0 / MIT |

## Troubleshooting

**Server not showing up in Claude Code?**
Restart Claude Code after modifying `~/.claude.json`. Check that the `skb` entry is not set to `"disabled": true`.

**Search returns no results?**
Run `/skb sync` first. Check `/skb status` to confirm your project is indexed.

**Wrong project detected?**
The server resolves the project from the Claude Code session's working directory via MCP roots. If you're in `/Users/you/projects/my-app`, the project name is `my-app`. Pass an explicit `project` parameter to `search_docs` if needed.

**ChromaDB errors on Python 3.14?**
ChromaDB doesn't yet support Python 3.14. Use Python 3.12 or 3.13. The `pyproject.toml` enforces `requires-python = ">=3.12,<3.14"`.
