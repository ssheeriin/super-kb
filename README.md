# SKB — Super Knowledge Base for Claude Code

[![CI](https://github.com/ssheeriin/super-kb/actions/workflows/ci.yml/badge.svg)](https://github.com/ssheeriin/super-kb/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/ssheeriin/super-kb)](https://github.com/ssheeriin/super-kb/releases)
[![License](https://img.shields.io/github/license/ssheeriin/super-kb)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.12%20%7C%203.13-blue)](pyproject.toml)

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

## Quick Start

For most users:

1. Install SKB with `install.sh` or `install.ps1`
2. Connect Claude Code with either:
   - `claude mcp add skb --scope user -- skb-mcp-server`
   - or a repo-scoped `.mcp.json`
3. Open a project in Claude and ask:
   `Provision SKB in this project`
4. Add documents to `.skb/`
5. Run `/skb sync` and start searching

## Installation

### Prerequisites

- Claude Code
- macOS, Linux, or Windows
- For the installer scripts:
  - macOS/Linux: `curl` or `wget`, `tar`
  - Windows: PowerShell with `Invoke-WebRequest` and `Expand-Archive`

### Install from GitHub Release with Installer Scripts

This is the recommended path for normal users, including Java developers who do
not use `uv`. The installer scripts download the correct standalone binary
bundle from the latest GitHub release, verify its checksum, and install
`skb-mcp-server` into a user-local location.

macOS or Linux:

```bash
curl -fsSL https://raw.githubusercontent.com/ssheeriin/super-kb/main/install.sh | bash
```

Windows PowerShell:

```powershell
irm https://raw.githubusercontent.com/ssheeriin/super-kb/main/install.ps1 | iex
```

Useful installer options:

- `--register-claude`
  Register `skb` globally in Claude Code after install
- `--bootstrap-model`
  Download and warm the embedding model immediately
- `--write-project-mcp <path>`
  Generate a project-scoped `.mcp.json` in a repo

Examples:

```bash
curl -fsSL https://raw.githubusercontent.com/ssheeriin/super-kb/main/install.sh | bash -s -- --register-claude --bootstrap-model
```

```powershell
irm https://raw.githubusercontent.com/ssheeriin/super-kb/main/install.ps1 | iex -RegisterClaude -BootstrapModel
```

### Verify the Install

Verify that the SKB executable is available:

```bash
skb-mcp-server version
```

You can also inspect the local install:

```bash
skb-mcp-server doctor
```

### Connect Claude Code

There are two supported setup modes.

#### Option A: User-Scoped MCP Setup

Use this if you want one SKB install to work across all your projects.

```bash
claude mcp add skb --scope user -- skb-mcp-server
```

Verify it:

```bash
claude mcp get skb
```

`skb-mcp-server` is not a placeholder. It is the real installed executable.

#### Option B: Project-Scoped `.mcp.json`

Use this for shared repositories, especially team-owned Java repos.

The repo does not need `.mcp.json` for SKB to work, but checking it in makes
the repo self-describing and avoids asking every developer to run a project-
specific Claude setup command.

Generate it in a repo:

```bash
skb-mcp-server write-mcp-config --project-root /path/to/project
```

That writes:

```json
{
  "mcpServers": {
    "skb": {
      "command": "skb-mcp-server",
      "args": []
    }
  }
}
```

See the Java example:

- [sample/java-project/.mcp.json](sample/java-project/.mcp.json)
- [sample/java-project/README.md](sample/java-project/README.md)

### Alternative: Install from a Wheel

If you already use Python packaging tools, you can still install a release
wheel directly.

```bash
uv tool install https://github.com/ssheeriin/super-kb/releases/download/v0.2.2/skb_mcp_server-0.2.2-py3-none-any.whl
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

The first sync on a machine may take a bit longer because SKB warms its local
embedding model and stores it under `~/.skb/`. If you want to do that ahead of
time, run:

```bash
skb-mcp-server bootstrap-model
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

### Standalone CLI Commands

These are useful outside Claude Code, especially for installation and team
setup.

| Command | Purpose |
|---------|---------|
| `skb-mcp-server serve` | Run the MCP server explicitly |
| `skb-mcp-server version` | Show installed version and platform |
| `skb-mcp-server doctor` | Inspect install state, Claude config, and optional project `.mcp.json` |
| `skb-mcp-server bootstrap-model` | Pre-download and warm the embedding model |
| `skb-mcp-server write-mcp-config` | Generate a project-scoped `.mcp.json` |

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
- If `skb-mcp-server` is not found after install, ensure the installer's bin directory is on `PATH`.
- If search returns nothing, sync the project first with `sync_skb` or `/skb sync`.
- The first sync can take longer on a new machine because SKB downloads and warms its local embedding model.
- Run `skb-mcp-server doctor` to inspect PATH, Claude configuration, the model cache, and optional project `.mcp.json`.
- Run `skb-mcp-server bootstrap-model` if you want to prefetch the local model before first sync.
- If you get a "No .skb/ folder found" error, provision the project first.
- If indexing behaves oddly after large changes, run `/skb reindex`.
- The wheel and source-checkout install paths support Python 3.12 or 3.13. The standalone binary installers do not require a separately managed Python runtime.

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

## Community

- [Contributing Guide](CONTRIBUTING.md)
- [Code of Conduct](CODE_OF_CONDUCT.md)
- [Support Guide](SUPPORT.md)
- [Security Policy](SECURITY.md)
- [Changelog](CHANGELOG.md)

## License

SKB is licensed under the [Apache License 2.0](LICENSE).

## More Documentation

For deeper details, see:

- [USERGUIDE.md](USERGUIDE.md)
- [sample/claude-config/SETUP.md](sample/claude-config/SETUP.md)
