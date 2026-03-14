# Implement Feature

Use this skill when the user wants a new feature or a substantial behavior change
implemented in `super-kb`.

## Workflow

1. Inspect the nearest existing pattern first.
2. Plan the change before editing if it spans multiple areas.
3. Work through the affected surfaces in this order when relevant:
   1. runtime module in `skb/`
   2. CLI or MCP wiring
   3. project templates or provisioning behavior
   4. tests
   5. packaging or release behavior
   6. docs
4. Keep behavior portable across installed, packaged, and source-checkout flows.

## Repository Expectations

- Update targeted tests when runtime behavior changes.
- Update clean-room or build validation when packaging behavior changes.
- Keep `sample/claude-config/` aligned with actual runtime templates if both
  represent the same product flow.
