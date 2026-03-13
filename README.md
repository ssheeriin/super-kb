# SKB — Super Knowledge Base for Claude Code

SKB is a local MCP server for Claude Code that turns a project's `.skb/` folder
into a searchable knowledge base. You drop in design docs, API references,
notes, and code examples, and Claude can search them without requiring `@`
mentions or manual file hunting.

Everything runs locally. SKB stores vectors in ChromaDB on your machine, uses a
local embedding model, and exposes MCP tools that Claude Code can call for
provisioning, syncing, searching, exporting, and importing project knowledge.

## What It Is

SKB is built around one simple workflow:

```text
project files in .skb/
        ->
local indexing and vector storage
        ->
Claude Code searches your project knowledge through MCP
```

Typical use cases:

- Architecture and design documents
- API references and onboarding notes
- Reusable code examples and patterns
- Technical decisions you want Claude to find later

## Installation

### Prerequisites

- Python 3.12 or 3.13
- `uv`
- Claude Code

### Install from GitHub Release

This is the recommended path for normal users.

1. Download the latest `.whl` asset from the GitHub Releases page.
2. Install it with `uv`:

```bash
uv tool install ./skb_mcp_server-<version>-py3-none-any.whl
```

3. Register the installed MCP server with Claude Code:

```bash
claude mcp add skb --scope user -- skb-mcp-server
```

4. Verify the registration:

```bash
claude mcp get skb
```

### Install from Source Checkout

Use this if you want to develop or modify SKB locally.

```bash
git clone https://github.com/ssheeriin/super-kb.git
```

Register the checkout with Claude Code:

```bash
claude mcp add skb --scope user -- uv --directory /path/to/super-kb run python -m skb
```

Verify the registration:

```bash
claude mcp get skb
```

### Optional Claude Configuration

SKB works once the MCP server is registered, but you can make the experience
better by adding Claude instructions and example skill files.

If you are using a source checkout, see:

- [sample/claude-config/SETUP.md](sample/claude-config/SETUP.md)
- [sample/claude-config/CLAUDE.md](sample/claude-config/CLAUDE.md)
- [sample/claude-config/skills/skb/SKILL.md](sample/claude-config/skills/skb/SKILL.md)

## Usage

### 1. Provision a Project

Open Claude Code in the project where you want to use SKB:

```bash
cd my-project
claude
```

Then ask Claude:

```text
Provision SKB in this project
```

That creates:

- `.skb/`
- `.claude/CLAUDE-skb.md`
- `.claude/skills/skb/SKILL.md`
- a `CLAUDE.md` import if needed

### 2. Add Files to `.skb/`

Example:

```text
my-project/
├── .skb/
│   ├── architecture.md
│   ├── api-reference.pdf
│   └── snippets/
│       └── retry.py
└── src/
```

Good candidates:

- architecture docs
- API specs
- onboarding notes
- code examples
- configuration references

### 3. Sync the Knowledge Base

Ask Claude to sync:

```text
Sync SKB for this project
```

Or, after provisioning installs the local skill:

```text
/skb sync
```

### 4. Search Docs and Code

Examples:

```text
How does our authentication flow work?
```

```text
Find the retry pattern we use for Python services
```

Or use the skill directly:

```text
/skb search authentication flow
/skb code retry lang:python
```

### 5. Reindex, Export, and Import

Common maintenance commands:

```text
/skb reindex
/skb docs
/skb export
/skb import <source-archive> <index-archive>
```

## Key Features

- Local-only storage and indexing
- Project-scoped knowledge via `.skb/`
- Incremental sync for changed files
- Semantic document search
- Code-only search with language filters
- Project provisioning through MCP
- Export and import for source archives and vector indexes

## Supported File Types

| Type | Extensions |
|------|------------|
| Markdown | `.md` |
| Plain text | `.txt`, `.rst` |
| PDF | `.pdf` |
| Code | `.py`, `.js`, `.ts`, `.java`, `.go`, `.rs` |
| Config | `.yaml`, `.yml`, `.json` |

## Commands and Tools

### Main MCP Tools

| Tool | Purpose |
|------|---------|
| `provision_skb` | Bootstrap SKB in the current project |
| `sync_skb` | Index or update files from `.skb/` |
| `search_docs` | Search project documentation semantically |
| `search_code` | Search code examples, optionally by language |
| `list_projects` | Show indexed projects |
| `list_documents` | Show indexed documents for a project |
| `reindex_project` | Rebuild a project's index from scratch |
| `remove_project` | Delete indexed data for a project |
| `export_skb` / `import_skb` | Export or import `.skb/` source files |
| `export_index` / `import_index` | Export or import vector index data |

### `/skb` Skill Commands

These are available after project provisioning installs the local skill.

| Command | Purpose |
|---------|---------|
| `/skb provision` | Provision the current project |
| `/skb sync` | Sync `.skb/` |
| `/skb search <query>` | Search docs |
| `/skb code <query> lang:<language>` | Search code |
| `/skb docs` | List indexed files |
| `/skb status` | List indexed projects |
| `/skb reindex` | Full reindex |
| `/skb export` | Export source and index |
| `/skb import ...` | Import source and index |

## Project Layout

### In a Provisioned Project

```text
my-project/
├── .skb/
├── CLAUDE.md
└── .claude/
    ├── CLAUDE-skb.md
    └── skills/
        └── skb/
            └── SKILL.md
```

### In This Repository

```text
super-kb/
├── pyproject.toml
├── README.md
├── USERGUIDE.md
├── sample/
├── tests/
└── skb/
    ├── __main__.py
    ├── server.py
    ├── provisioning.py
    ├── sync.py
    ├── tools.py
    ├── store.py
    ├── ingest.py
    ├── embeddings.py
    ├── reranker.py
    ├── templates/
    └── chunkers/
```

## Troubleshooting

- If Claude does not see SKB, run `claude mcp get skb` and restart Claude Code.
- If search returns nothing, sync the project first with `sync_skb` or `/skb sync`.
- If you get a "No .skb/ folder found" error, provision the project first.
- If indexing behaves oddly after large changes, run `/skb reindex`.
- Use Python 3.12 or 3.13. The project does not support Python 3.14.

## Development

Run the server from a source checkout:

```bash
uv --directory /path/to/super-kb run python -m skb
```

Run tests:

```bash
uv run --with pytest --with build pytest -q
```

The release workflow lives in `.github/workflows/release.yml` and validates the
test suite before publishing GitHub release artifacts.

## More Documentation

For deeper details, see:

- [USERGUIDE.md](USERGUIDE.md)
- [sample/claude-config/SETUP.md](sample/claude-config/SETUP.md)
