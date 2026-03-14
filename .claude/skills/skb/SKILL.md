---
name: "skb"
description: "Search and manage the local Super Knowledge Base (.skb), including provisioning, sync, search, reindex, export, and import."
argument-hint: "provision [--force] | search <query> | code <query> [lang:<language>] | sync | reindex [project] | status | docs | export [path] | export-source [path] | export-index [path] | import <source_path> <index_path> | import-source <path> [--replace] | import-index <path> | help"
disable-model-invocation: true
---

# Super Knowledge Base

Use this skill when the user wants to provision, sync, search, reindex, export,
or import the local project knowledge base in `.skb/`.

## Core MCP Mapping

- `provision` -> `mcp__skb__provision_skb`
- `search <query>` -> `mcp__skb__search_docs`
- `code <query>` -> `mcp__skb__search_code`
- `sync` -> `mcp__skb__sync_skb`
- `reindex` -> `mcp__skb__reindex_project`
- `status` -> `mcp__skb__list_projects`
- `docs` -> `mcp__skb__list_documents`
- `export` -> export source plus index
- `import` -> import source plus index

## Behavior

- Search indexed docs before asking the user to restate repository context that
  may already exist in `.skb/`.
- Use full reindex only when the user asks for it or the incremental index is
  clearly stale.
