## Super Knowledge Base (.skb/)

A local vector knowledge base is available via MCP tools prefixed with
`mcp__skb__`.

### When to use

- Sync the knowledge base when the repository docs or local `.skb/` content may
  have changed.
- Use `mcp__skb__search_docs` before asking the user to restate repo
  documentation that may already be indexed.
- Use `mcp__skb__search_code` when you want examples of install flows, packaging
  logic, or provisioning behavior.

### Adding to the knowledge base

- When the user wants repository context persisted, place it in `.skb/` and then
  sync the project.
- Supported file types include markdown, text, PDF, code, YAML, and JSON.
