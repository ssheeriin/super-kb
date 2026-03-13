---
name: skb
description: Search and manage the Super Knowledge Base (.skb). Use when you want to provision, sync, search, reindex, export, or import the knowledge base.
argument-hint: provision [--force] | search <query> | code <query> [lang:<language>] | sync | reindex [project] | status | docs | export [path] | export-source [path] | export-index [path] | import <source_path> <index_path> | import-source <path> [--replace] | import-index <path> | help
disable-model-invocation: true
---

Search or manage the super knowledge base (.skb/ folder).

Usage:
- `/skb provision` - Provision SKB in the current project by creating `.skb/`, installing the local skill, and wiring project instructions
- `/skb provision --force` - Re-apply the generated SKB files even if the local copies differ
- `/skb search <query>` - Search the knowledge base for relevant docs
- `/skb code <query>` - Search for code examples (optionally: `/skb code <query> lang:<language>`)
- `/skb sync` - Incrementally sync the current project's .skb/ folder
- `/skb reindex` - Force a full reindex (delete + rebuild) of the current project
- `/skb reindex <project>` - Force a full reindex of a specific project by name
- `/skb status` - Show indexed projects and document counts
- `/skb docs` - List all indexed files for the current project
- `/skb export` - Export both source files (.tar.gz) and vector index (.jsonl.gz)
- `/skb export-source` - Export only .skb/ source files as a .tar.gz
- `/skb export-index` - Export only the vector index as .jsonl.gz
- `/skb import <source_path> <index_path>` - Import both source and index archives
- `/skb import-source <path>` - Import a .tar.gz source archive into .skb/ and sync
- `/skb import-source <path> --replace` - Import replacing existing .skb/ instead of merging
- `/skb import-index <path>` - Import a .jsonl.gz index archive into ChromaDB
- `/skb help` - Show this help

Interpret the user's argument and call the appropriate MCP tool:
- For `provision`: call `mcp__skb__provision_skb`.
- For `provision --force`: call `mcp__skb__provision_skb` with `force=True`.
- For `search <query>`: call `mcp__skb__search_docs` with the query.
- For `code <query>`: call `mcp__skb__search_code` with the query. If `lang:<language>` is present, pass the language filter.
- For `sync`: call `mcp__skb__sync_skb`.
- For `reindex`: call `mcp__skb__reindex_project` with no arguments for the current project.
- For `reindex <project>`: call `mcp__skb__reindex_project` with `project=<project>`.
- For `status`: call `mcp__skb__list_projects`.
- For `docs`: call `mcp__skb__list_documents`.
- For `export`: call both `mcp__skb__export_skb` and `mcp__skb__export_index` for the current project and default paths.
- For `export-source`: call `mcp__skb__export_skb` only.
- For `export-source <path>`: call `mcp__skb__export_skb` with `output_path=<path>`.
- For `export-index`: call `mcp__skb__export_index` only.
- For `export-index <path>`: call `mcp__skb__export_index` with `output_path=<path>`.
- For `import <source_path> <index_path>`: call `mcp__skb__import_skb` with `archive_path=<source_path>` and `run_sync=False`, then call `mcp__skb__import_index` with `archive_path=<index_path>`.
- For `import-source <path>`: call `mcp__skb__import_skb` with `archive_path=<path>` and `merge=True`.
- For `import-source <path> --replace`: call `mcp__skb__import_skb` with `archive_path=<path>` and `merge=False`.
- For `import-index <path>`: call `mcp__skb__import_index` with `archive_path=<path>`.
- For no argument or `help`: show the usage list above.

Arguments: $ARGUMENTS
