# SKB User Guide — Super Knowledge Base for Claude Code

## Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Installation & Configuration](#installation--configuration)
- [Quick Start](#quick-start)
- [How It Works](#how-it-works)
  - [Architecture](#architecture)
  - [How Claude Detects `.skb/` and Auto-Indexes](#how-claude-detects-skb-and-auto-indexes)
  - [Incremental Sync Pipeline](#incremental-sync-pipeline)
  - [Chunking Strategies](#chunking-strategies)
  - [Vector Storage](#vector-storage)
- [MCP Tools Reference](#mcp-tools-reference)
- [Supported File Types](#supported-file-types)
- [Common Workflows](#common-workflows)
- [Project Structure](#project-structure)
- [Troubleshooting](#troubleshooting)

---

## Overview

SKB (Super Knowledge Base) is a local MCP server that turns `.skb/` folders in your projects into a searchable vector knowledge base for Claude Code. You drop documentation, code snippets, design docs, and API specs into a `.skb/` folder, and Claude can find and use them automatically — no `@` file mentions needed.

Everything runs locally. No external APIs, no cloud services. Documents are embedded using BAAI/bge-small-en-v1.5 (a custom ONNX model) and stored on your machine.

---

## Prerequisites

| Requirement | Version | Notes |
|-------------|---------|-------|
| **Python** | 3.12 or 3.13 | ChromaDB does not yet support 3.14 |
| **uv** | Latest | [Install uv](https://docs.astral.sh/uv/) — the fast Python package manager |
| **Claude Code** | Latest | The Claude Code CLI (`claude`) |

> **Note:** You do NOT need to run `pip install` or `uv pip install`. Dependencies are installed automatically on first run via `uv run`.

---

## Installation & Configuration

### Step 1: Clone the Repository

```bash
git clone https://github.com/ssheeriin/super-kb.git
```

### Step 2: Register the MCP Server with Claude Code

Register the server using Claude Code's MCP CLI:

```bash
claude mcp add skb --scope user -- uv --directory /path/to/super-kb run python -m skb
```

Replace `/path/to/super-kb` with the actual path where you cloned the repository (e.g., `/Users/yourname/dev/super-kb`).
Use `--scope user` so SKB is available in every project on your machine.

If you installed SKB from a GitHub release artifact, register the installed executable instead:

```bash
claude mcp add skb --scope user -- skb-mcp-server
```

Verify the registration:

```bash
claude mcp get skb
```

If SKB is already connected in a Claude session, you can ask Claude to
"provision SKB in this project" and it will call `provision_skb` to create:
- `.skb/`
- `.claude/CLAUDE-skb.md`
- `.claude/skills/skb/SKILL.md`
- a `CLAUDE.md` import if one is missing

### Step 3: Configure Claude Code Instructions (Recommended)

To make Claude **proactively** sync and search your knowledge base, add instructions to `~/.claude/CLAUDE.md`:

```markdown
## Knowledge Base

When starting a session in a project that has a `.skb/` folder:
1. Call `sync_skb` to index/update the knowledge base.
2. When answering questions about the project, search the knowledge base first
   using `search_docs` or `search_code` before asking the user for files.
3. If the user mentions adding new files to `.skb/`, call `sync_skb` again.
```

This is the key mechanism that makes the auto-detection and auto-indexing feel "automatic" — Claude reads these instructions and proactively calls the tools.

### Step 4: Optional - Install the `skb` Skill

```bash
mkdir -p ~/.claude/skills/skb
cp sample/claude-config/skills/skb/SKILL.md ~/.claude/skills/skb/SKILL.md
```

This gives you `/skb search`, `/skb sync`, `/skb reindex`, `/skb export`, `/skb import`, and related shortcuts.

### Step 5: Start or Restart Claude Code

Start or restart Claude Code so it picks up the new MCP server and any new skill files.

---

## Quick Start

### 1. Create a `.skb/` folder in your project

```bash
mkdir my-project/.skb
```

### 2. Drop in your context files

```bash
cp architecture.md  my-project/.skb/
cp api-reference.pdf my-project/.skb/
cp auth-example.py   my-project/.skb/
```

### 3. Start Claude Code in that project

```bash
cd my-project
claude
```

### 4. Claude automatically syncs and searches

If you configured `CLAUDE.md` (Step 3 above), Claude will call `sync_skb` at session start and use `search_docs`/`search_code` to answer questions using your documents.

If you didn't configure `CLAUDE.md`, you can manually trigger sync:

```
> "Please sync the .skb/ knowledge base"
```

### 5. Ask questions

```
> "How does our authentication flow work?"
> "Show me an example of the retry pattern we use"
> "What does the API spec say about rate limiting?"
```

Claude will search your indexed documents and answer from them.

---

## How It Works

### Architecture

```
my-project/
├── .skb/                        ← You drop files here
│   ├── architecture.md
│   ├── api-reference.pdf
│   └── snippets/
│       └── retry-logic.py
├── src/
└── ...

         ↓ sync_skb tool call

┌─────────────────────────────────────────────────────┐
│  SKB MCP Server (stdio)                             │
│                                                     │
│  1. Scan .skb/ for files          (sync.py)         │
│  2. Detect type by extension      (config.py)       │
│  3. Extract text content          (ingest.py)       │
│  4. Chunk by type                 (chunkers/*.py)   │
│  5. Embed & store in ChromaDB     (store.py)        │
│  6. Rerank results with FlashRank (reranker.py)     │
│                                                     │
│  ChromaDB (local, on disk)                          │
│  Location: ~/.skb/chromadb/                         │
└─────────────────────────────────────────────────────┘

         ↓ search_docs / search_code tool calls

    Claude Code reads results and answers your questions
```

### How Claude Detects `.skb/` and Auto-Indexes

Claude's "automatic" detection is driven by three layers working together:

#### Layer 1: MCP Server Instructions

When the SKB server starts, it provides instructions to Claude via the `FastMCP` initialization:

> *"Each project may have a .skb/ folder with context documents. Use sync_skb to index them, then search_docs/search_code to query."*

These instructions are part of the MCP protocol — Claude receives them when it connects to the server.

#### Layer 2: CLAUDE.md System Prompt

The instructions in `~/.claude/CLAUDE.md` (configured in Step 3 of Installation) tell Claude to:
- Call `sync_skb` at session start
- Search the knowledge base before asking the user for files
- Re-sync when the user mentions adding new files

This is what makes the behavior feel "automatic" — Claude reads these instructions and proactively invokes the tools.

#### Layer 3: Convention-Based Discovery

The `sync_skb` tool resolves the project directory (from `Path.cwd()` or an explicit argument) and looks for a `.skb/` subfolder. If found, it scans and ingests. If not found, it returns an error message — no crash, just a note.

```
sync_skb called
    → project_dir = /Users/you/my-project
    → looks for /Users/you/my-project/.skb/
    → if exists: scan, chunk, embed, store
    → if missing: return { "error": "No .skb/ folder found" }
```

### Incremental Sync Pipeline

The sync process (`skb/sync.py`) is designed to be efficient on repeat calls:

| Scenario | Action |
|----------|--------|
| **New file** in `.skb/` | Ingest: extract → chunk → embed → store |
| **Modified file** (mtime changed) | Delete old chunks, re-ingest from scratch |
| **Unchanged file** (same mtime) | Skip entirely — no work done |
| **Deleted file** (was indexed, no longer on disk) | Remove its chunks from ChromaDB |

The comparison key is the file's **modification timestamp** (`st_mtime`), stored as metadata in ChromaDB. This means:

- Touching a file (changing mtime without changing content) will trigger re-ingestion
- Copying a file with preserved mtime will be treated as unchanged

### Chunking Strategies

Each file type has a specialized chunker that understands its structure:

#### Markdown (`skb/chunkers/markdown.py`)
- Splits on `#`, `##`, `###`, `####` headers
- Each header section becomes a chunk
- Large sections (>1000 chars) are recursively split at paragraph boundaries
- Section titles are preserved as metadata

#### Code (`skb/chunkers/code.py`)
- Detects function/class boundaries using language-specific regex patterns
- Supported languages: Python, JavaScript, TypeScript, Java, Go, Rust
- Small files (≤1500 chars) are kept as a single chunk
- Large functions are split at line boundaries with overlap
- Falls back to generic patterns for unknown languages

#### Text / Config (`skb/chunkers/text.py`)
- Recursive character split at natural boundaries: `\n\n` → `\n` → `. ` → ` `
- Config files (YAML, JSON) under 3000 chars are kept whole
- Text files use 1000-char chunks with 200-char overlap

#### PDF (`skb/chunkers/pdf.py`)
- Text extracted via `pypdf` in `ingest.py` (page by page)
- Extracted text is then split using the same recursive character strategy as text
- 1000-char chunks with 200-char overlap

#### Chunk Size Reference

| Doc Type | Max Chunk Size | Overlap |
|----------|---------------|---------|
| Markdown | 1000 chars | 200 chars |
| Text | 1000 chars | 200 chars |
| PDF | 1000 chars | 200 chars |
| Code | 1500 chars | 200 chars |
| Config | 3000 chars | 0 chars |

### Vector Storage

- **Engine**: [ChromaDB](https://www.trychroma.com/) with persistent local storage
- **Location**: `~/.skb/chromadb/` (configurable via `SKB_HOME` env var)
- **Embedding model**: BAAI/bge-small-en-v1.5 (384d, custom ONNX) — downloaded on first run to `~/.skb/models/`
- **Reranking**: FlashRank cross-encoder (ms-marco-TinyBERT-L-2-v2) for improved search relevance
- **Similarity metric**: Cosine distance
- **Organization**: One ChromaDB collection per project (named after the project directory)
- **Telemetry**: Disabled (`anonymized_telemetry=False`)

> **Upgrade note:** If upgrading from a previous version, existing indexes must be reindexed (`reindex_project` tool or `/skb reindex`) because the embedding model changed from all-MiniLM-L6-v2 to bge-small-en-v1.5. Old vectors are incompatible with the new model.

Each stored chunk includes metadata:
- `source` — relative file path within the project
- `project` — project name (directory name)
- `doc_type` — markdown / text / code / pdf / config
- `section` — header text for markdown, empty for other types
- `language` — programming language (for code files)
- `chunk_index` / `total_chunks` — position within the source file
- `ingested_at` — UTC timestamp of indexing
- `file_modified_at` — file's modification time at ingest

---

## MCP Tools Reference

### `provision_skb`

Provision SKB into the current project by creating `.skb/`, installing the
project-local skill, writing `.claude/CLAUDE-skb.md`, and wiring `CLAUDE.md`
to import it.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `project_dir` | string | Current working directory | Path to the project root |
| `force` | bool | false | Overwrite generated SKB files when they differ from the templates |

**Example response:**
```json
{
  "project": "my-project",
  "created_directories": [".skb", ".claude/skills/skb"],
  "created_files": [
    ".claude/CLAUDE-skb.md",
    ".claude/skills/skb/SKILL.md",
    "CLAUDE.md"
  ],
  "updated_files": [],
  "skipped_files": [],
  "next_steps": [
    "Add project documents to .skb/",
    "Restart Claude Code or open a new session to load the local skill and project CLAUDE.md",
    "Run sync_skb after adding files to .skb/"
  ]
}
```

---

### `sync_skb`

Scan the `.skb/` folder and ingest/update all files. Incremental — only processes changes.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `project_dir` | string | Current working directory | Path to the project root |

**Example response:**
```json
{
  "project": "my-project",
  "files_added": 3,
  "files_updated": 1,
  "files_removed": 0,
  "files_failed": 0,
  "total_chunks": 24
}
```

---

### `search_docs`

Semantic search across project documentation.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `query` | string | *(required)* | What to search for |
| `n_results` | int | 5 | Number of results to return |
| `project` | string | Current project | Which project to search |
| `search_all_projects` | bool | false | Search across all indexed projects |

**Example response:**
```json
{
  "query": "authentication flow",
  "results": [
    {
      "content": "## Authentication\n\nThe API uses OAuth2...",
      "score": 0.87,
      "source_file": ".skb/api-reference.md",
      "project": "my-project",
      "doc_type": "markdown",
      "section": "## Authentication",
      "language": null
    }
  ],
  "count": 1,
  "scope": "my-project"
}
```

---

### `search_code`

Search filtered to code files only, with optional language filter.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `query` | string | *(required)* | What code to search for |
| `language` | string | `""` (any) | Filter by language: `python`, `javascript`, etc. |
| `n_results` | int | 5 | Number of results to return |

**Example response:**
```json
{
  "query": "retry logic",
  "language": "python",
  "results": [
    {
      "content": "def retry_with_backoff(func, max_retries=3):\n    ...",
      "score": 0.82,
      "source_file": ".skb/snippets/retry-logic.py",
      "project": "my-project",
      "doc_type": "code",
      "section": "",
      "language": "python"
    }
  ],
  "count": 1
}
```

---

### `list_projects`

Show all indexed projects with chunk counts.

*No parameters.*

**Example response:**
```json
{
  "projects": [
    { "project": "my-project", "chunk_count": 24 },
    { "project": "other-project", "chunk_count": 12 }
  ],
  "total_projects": 2
}
```

---

### `list_documents`

List indexed files for a project with metadata.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `project` | string | Current project | Which project to list |

**Example response:**
```json
{
  "project": "my-project",
  "documents": [
    {
      "source": ".skb/architecture.md",
      "doc_type": "markdown",
      "chunk_count": 8,
      "ingested_at": "2026-03-06T19:30:00+00:00",
      "file_modified_at": "2026-03-05T14:22:00+00:00"
    }
  ],
  "total_documents": 1
}
```

---

### `remove_project`

Delete all indexed data for a project.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `project` | string | *(required)* | Name of the project to remove |

**Example response:**
```json
{
  "project": "my-project",
  "removed": true,
  "message": "Project 'my-project' removed."
}
```

---

### `reindex_project`

Force a full reindex: delete all indexed data for a project and rebuild from scratch. Use when the index is corrupted, embeddings need regenerating (e.g., after an embedding model upgrade), or you want a clean slate.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `project` | string | `""` | Project name — used to look up the directory from stored metadata |
| `project_dir` | string | `""` | Explicit path to project root — takes precedence over project name |

If both are empty, defaults to the current working directory.

**Example response:**
```json
{
  "project": "my-project",
  "files_added": 5,
  "files_updated": 0,
  "files_removed": 0,
  "files_failed": 0,
  "total_chunks": 42
}
```

---

## Supported File Types

| Type | Extensions | Chunking Strategy | Max Chunk Size |
|------|-----------|-------------------|---------------|
| Markdown | `.md` | Split on `#`/`##`/`###`/`####` headers, recursive split for large sections | 1000 chars |
| Plain text | `.txt`, `.rst` | Recursive split at paragraph boundaries | 1000 chars |
| PDF | `.pdf` | Page extraction via `pypdf`, then recursive split | 1000 chars |
| Code | `.py`, `.js`, `.ts`, `.java`, `.go`, `.rs` | Function/class boundary detection (language-specific regex) | 1500 chars |
| Config | `.yaml`, `.yml`, `.json` | Whole file if small; recursive split if large | 3000 chars |

Unsupported file extensions are silently skipped during sync.

---

## Common Workflows

### Starting a New Session

```
> cd my-project && claude
# Claude automatically calls sync_skb (if CLAUDE.md is configured)
# Then searches knowledge base as needed during conversation
```

### Adding Files Mid-Session

```bash
# In another terminal:
cp new-design-doc.md my-project/.skb/
```

Then in Claude Code:

```
> "I added new-design-doc.md to .skb/, please sync"
```

Claude will call `sync_skb` and the new file will be indexed.

### Cross-Project Search

By default, searches are scoped to the current project directory. To search across all indexed projects:

```
> "Search all my projects for how we handle database migrations"
```

Claude will call `search_docs` with `search_all_projects=true`.

### Removing a Project's Index

```
> "Remove the old-project knowledge base"
```

Claude will call `remove_project(project="old-project")`.

### Checking Index Status

```
> "What projects are indexed? Show me the status."
```

Claude will call `list_projects` and `list_documents`.

### Organizing `.skb/` with Subdirectories

Subdirectories within `.skb/` are supported and scanned recursively:

```
.skb/
├── design/
│   ├── architecture.md
│   └── data-model.md
├── api/
│   └── openapi-spec.yaml
└── examples/
    ├── auth-flow.py
    └── retry-pattern.ts
```

---

## What Goes in `.skb/`

**Good candidates:**
- Architecture and design documents
- API references and specifications
- Setup and onboarding notes
- Code snippets and patterns for reference
- Configuration examples
- Meeting notes with technical decisions
- Style guides and coding conventions

**Don't put in `.skb/`:**
- Binary files or images (not supported)
- `node_modules` or build artifacts
- Secrets or credentials
- Very large files (>1MB) — chunk quality degrades
- Files that change every few seconds (constant re-indexing)

**Git strategy:**
- Add `.skb/` to `.gitignore` if the docs are personal notes
- Commit `.skb/` if you want to share project context with your team

---

## Project Structure

```
super-kb/
├── pyproject.toml              # Project metadata and dependencies (incl. flashrank)
├── README.md                   # High-level overview and setup
├── USERGUIDE.md                # Detailed usage and architecture guide
├── tests/                      # Integration and provisioning tests
├── skb/
│   ├── __init__.py             # Package marker
│   ├── __main__.py             # `python -m skb` entry point
│   ├── server.py               # MCP server entry point (FastMCP server)
│   ├── config.py               # Constants: paths, extension maps, chunk sizes
│   ├── store.py                # ChromaDB wrapper (collections, queries, CRUD)
│   ├── embeddings.py           # Custom ONNX embedding function (bge-small-en-v1.5)
│   ├── reranker.py             # FlashRank cross-encoder reranker
│   ├── ingest.py               # File → content → chunks → vector store pipeline
│   ├── sync.py                 # .skb/ folder scanner, incremental sync logic
│   ├── tools.py                # MCP tool implementations (called by the server entry point)
│   ├── templates/              # Bundled provisioning templates
│   └── chunkers/
│       ├── __init__.py         # Dispatcher: routes doc_type to chunker
│       ├── markdown.py         # Header-aware markdown splitting
│       ├── code.py             # Function/class boundary splitting (6 languages)
│       ├── text.py             # Paragraph-based recursive splitting
│       └── pdf.py              # PDF text splitting (extraction in ingest.py)
├── sample/                     # Example Claude Code config files
└── uv.lock                     # Dependency lock file
```

### Key Files Explained

| File | Role |
|------|------|
| `skb/server.py` | Entry point. Creates a `FastMCP` server, registers the 12 MCP tools, and runs via `mcp.run()`. Invoked with `python -m skb` or the installed `skb-mcp-server` command. |
| `skb/__main__.py` | Thin module entry point so `python -m skb` runs the package directly. |
| `skb/config.py` | All constants in one place: ChromaDB path, supported extensions, language detection, chunk sizes and overlaps. |
| `skb/store.py` | Wraps ChromaDB operations: create/get collections, upsert documents, query by text with cosine similarity, delete by source file, list collections and documents. One collection per project. |
| `skb/embeddings.py` | Custom ONNX embedding function using BAAI/bge-small-en-v1.5. Downloads the model on first run to `~/.skb/models/`. Produces 384-dimensional vectors with L2 normalization. |
| `skb/reranker.py` | FlashRank cross-encoder reranker. Re-scores initial retrieval results for better relevance before returning to the user. Configurable via environment variables. |
| `skb/ingest.py` | Takes a single file, detects its type, extracts text (with `pypdf` for PDFs), calls the chunker, builds metadata, and upserts into ChromaDB. |
| `skb/sync.py` | Scans `.skb/` recursively, compares disk files against indexed files by modification time, and orchestrates add/update/remove operations via `ingest.py` and `store.py`. |
| `skb/tools.py` | Thin wrappers that translate MCP tool calls into `sync.py` and `store.py` function calls. Handles default project resolution from `Path.cwd()`. |

---

## Troubleshooting

### Server not showing up in Claude Code

- Run `claude mcp list` or `claude mcp get skb` to confirm the server is registered
- Check Claude Code's MCP connection status with `/mcp`
- Restart Claude Code after adding the server or skill file
- Test manually from a checkout: `uv --directory /path/to/super-kb run python -m skb` — it should start without errors
- Test manually from an installed release: `skb-mcp-server`

### Search returns no results

- Run `sync_skb` first (or ask Claude to sync)
- Check `list_projects` to confirm your project is indexed
- Check `list_documents` to see which files are indexed
- Verify your `.skb/` folder contains files with supported extensions

### Wrong project detected

- The server resolves the project from the Claude Code session's working directory via MCP roots
- If you're in `/Users/you/projects/my-app`, the project name is `my-app`
- Pass an explicit `project` parameter to `search_docs` if needed

### ChromaDB errors on Python 3.14

ChromaDB does not yet support Python 3.14. The `pyproject.toml` enforces `requires-python = ">=3.12,<3.14"`. Use Python 3.12 or 3.13.

### "No .skb/ folder found" error

- Ensure the `.skb/` directory exists in your project root (not nested inside `src/` or elsewhere)
- The folder name must be exactly `.skb` (lowercase, with the leading dot)

### Files not being re-indexed after changes

- SKB compares file modification times. If you edit a file in-place, its mtime should update and trigger re-indexing on the next `sync_skb` call
- If you copied a file preserving the original mtime, SKB may think it's unchanged — use `touch filename` to update the mtime

### Large files producing poor search results

Files over ~1MB tend to produce many chunks with diluted semantic meaning. Consider:
- Splitting the file into smaller, focused documents
- Extracting only the relevant sections into `.skb/`

---

## Technology Stack

| Component | Package | License | Purpose |
|-----------|---------|---------|---------|
| MCP SDK | `mcp` (FastMCP) | MIT | Claude Code ↔ server communication |
| Vector store | ChromaDB | Apache 2.0 | Local embedding storage and similarity search |
| Embeddings | BAAI/bge-small-en-v1.5 (custom ONNX) | MIT | 384-dimensional vectors, runs locally |
| Reranker | FlashRank (`flashrank`) | Apache 2.0 | Cross-encoder reranking for improved relevance |
| PDF parsing | pypdf | BSD-3-Clause | Extract text from PDF files |
| Package manager | uv | Apache 2.0 / MIT | Dependency management and script runner |

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SKB_HOME` | `~/.skb` | Base directory for all SKB data (ChromaDB, models) |
| `SKB_RERANK_ENABLED` | `true` | Enable/disable FlashRank reranking |
| `SKB_RERANK_MODEL` | `ms-marco-TinyBERT-L-2-v2` | FlashRank model name |
| `SKB_RERANK_MAX_LENGTH` | `512` | Max input length for reranker |
| `SKB_RERANK_RETRIEVAL_MULTIPLIER` | `3` | Fetch N\u00d7results before reranking (e.g., 3\u00d75 = 15 candidates reranked to return top 5) |
