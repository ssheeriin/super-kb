Search or manage the shared knowledge base (.skb/ folder).

Usage:
- `/skb search <query>` — Search the knowledge base for relevant docs
- `/skb code <query>` — Search for code examples (optionally: `/skb code <query> lang:<language>`)
- `/skb sync` — Incrementally sync the current project's .skb/ folder
- `/skb reindex` — Force a full reindex (delete + rebuild) of the current project
- `/skb reindex <project>` — Force a full reindex of a specific project by name
- `/skb status` — Show indexed projects and document counts
- `/skb docs` — List all indexed files for the current project
- `/skb help` — Show this help

Interpret the user's argument and call the appropriate MCP tool:
- For "search <query>": call mcp__skb__search_docs with the query
- For "code <query>": call mcp__skb__search_code with the query. If "lang:<language>" is present, pass the language filter.
- For "sync": call mcp__skb__sync_skb
- For "reindex": call mcp__skb__reindex_project (no args = current project)
- For "reindex <project>": call mcp__skb__reindex_project with project=<project>
- For "status": call mcp__skb__list_projects
- For "docs": call mcp__skb__list_documents
- For no argument or "help": show the usage list above

Arguments: $ARGUMENTS
