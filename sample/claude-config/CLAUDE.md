## Shared Knowledge Base (.skb/)

A local vector knowledge base is available via MCP tools prefixed with `mcp__skb__`.
Each project may have a `.skb/` folder containing context documents (design docs,
API refs, architecture notes, code snippets). These are automatically indexed in a
local vector store.

### When to use
- ALWAYS call `mcp__skb__sync_skb` at the start of a session to ensure the
  knowledge base is up to date with the project's `.skb/` folder.
- Use `mcp__skb__search_docs` to find relevant project documentation BEFORE
  asking the user to provide files or context. This replaces @ mentioning files.
- Use `mcp__skb__search_code` to find code examples and reference implementations.
- When the user mentions architecture, design decisions, API patterns, or project
  conventions — search the knowledge base first.

### Adding to the knowledge base
- When the user says "add this to the knowledge base" or "remember this", tell them
  to save the file in the project's `.skb/` folder, then call `sync_skb`.
- Supported file types: .md, .txt, .pdf, .py, .js, .ts, .java, .go, .rs, .yaml, .json, .rst

### Cross-project search
- By default, search is scoped to the current project.
- Use `search_all_projects=true` when the user asks about patterns across projects
  or references another project's docs.
