# Clean-Room Smoke

Use this skill when the user wants SKB validated from a fresh environment or when
install, packaging, provisioning, or first-run behavior changed.

## Workflow

1. Start from the smallest isolated environment practical:
   - clean temp project
   - clean temp home or install root
   - released artifact or local built artifact, depending on the task
2. Exercise the end-user flow that changed:
   - install
   - optional Claude registration
   - project provisioning
   - add a dummy `.skb/` document
   - sync
   - search or list docs
3. Report exactly which path was tested:
   - source checkout
   - wheel install
   - standalone binary
   - installer script

## Output

- Be explicit about what was and was not validated.
- Call out platform limits if Linux or Windows were not manually exercised.
