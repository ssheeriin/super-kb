---
name: "docs-sync"
description: "Keep README, USERGUIDE, sample Claude config, and release-facing docs aligned with runtime or packaging changes."
---

# Docs Sync

Use this skill when runtime behavior, packaging, install flow, release assets, or
project setup behavior changed and documentation must stay aligned.

## Primary Targets

- `README.md`
- `USERGUIDE.md`
- `CHANGELOG.md`
- `sample/claude-config/`
- release-facing installer and uninstaller examples

## Workflow

1. Identify the user-visible change from code or scripts.
2. Update only the documentation that is directly affected.
3. Keep examples copy-pasteable.
4. Avoid hardcoded local filesystem paths unless the text is explicitly about a
   local developer workflow and uses a placeholder path.

## Output

- Keep install docs concise.
- Keep advanced operational detail in `USERGUIDE.md`, not in the README unless it
  is part of the main user journey.
