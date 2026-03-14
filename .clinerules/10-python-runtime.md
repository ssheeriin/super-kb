---
paths:
  - "skb/**"
  - "tests/**"
  - "pyproject.toml"
  - "scripts/**"
---

# Python Runtime Rules

- Keep runtime behavior in `skb/`.
- Update or add tests when changing CLI, MCP server, provisioning, portability,
  or indexing behavior.
- Prefer focused tests first, then broader `pytest` coverage if the change
  affects packaging or entrypoints.
- Keep runtime templates and project-scoped config helpers consistent with the
  behavior described in the docs.
