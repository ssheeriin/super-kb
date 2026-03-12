Search or manage the super knowledge base (.skb/ folder).

Usage:
- `/skb search <query>` — Search the knowledge base for relevant docs
- `/skb code <query>` — Search for code examples (optionally: `/skb code <query> lang:<language>`)
- `/skb sync` — Incrementally sync the current project's .skb/ folder
- `/skb reindex` — Force a full reindex (delete + rebuild) of the current project
- `/skb reindex <project>` — Force a full reindex of a specific project by name
- `/skb status` — Show indexed projects and document counts
- `/skb docs` — List all indexed files for the current project
- `/skb export` — Export both source files (.tar.gz) and vector index (.jsonl.gz)
- `/skb export-source` — Export only .skb/ source files as a .tar.gz
- `/skb export-index` — Export only the vector index as .jsonl.gz
- `/skb import <source_path> <index_path>` — Import both source and index archives
- `/skb import-source <path>` — Import a .tar.gz source archive into .skb/ and sync
- `/skb import-source <path> --replace` — Import replacing existing .skb/ (instead of merging)
- `/skb import-index <path>` — Import a .jsonl.gz index archive into ChromaDB
- `/skb help` — Show this help

Interpret the user's argument and call the appropriate MCP tool:
- For "search <query>": call mcp__skb__search_docs with the query
- For "code <query>": call mcp__skb__search_code with the query. If "lang:<language>" is present, pass the language filter.
- For "sync": call mcp__skb__sync_skb
- For "reindex": call mcp__skb__reindex_project (no args = current project)
- For "reindex <project>": call mcp__skb__reindex_project with project=<project>
- For "status": call mcp__skb__list_projects
- For "docs": call mcp__skb__list_documents
- For "export": call BOTH mcp__skb__export_skb AND mcp__skb__export_index (current project, default paths)
- For "export-source": call mcp__skb__export_skb only
- For "export-source <path>": call mcp__skb__export_skb with output_path=<path>
- For "export-index": call mcp__skb__export_index only
- For "export-index <path>": call mcp__skb__export_index with output_path=<path>
- For "import <source_path> <index_path>": call mcp__skb__import_skb with archive_path=<source_path> and run_sync=False, THEN call mcp__skb__import_index with archive_path=<index_path>
- For "import-source <path>": call mcp__skb__import_skb with archive_path=<path>, merge=True
- For "import-source <path> --replace": call mcp__skb__import_skb with archive_path=<path>, merge=False
- For "import-index <path>": call mcp__skb__import_index with archive_path=<path>
- For no argument or "help": show the usage list above

Arguments: $ARGUMENTS
