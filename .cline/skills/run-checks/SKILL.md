---
name: "run-checks"
description: "Run the super-kb validation commands, especially pytest, build-validation, and Python syntax checks."
---

# Run Checks

Use this skill when the user wants SKB validation run and summarized.

## Default Commands

```bash
python3 -m py_compile skb/*.py skb/chunkers/*.py tests/*.py scripts/*.py
uv run --with pytest pytest -q
```

## Broader Validation

Use this when packaging or release behavior changed:

```bash
uv run --with pytest --with build pytest -q
```

## Reporting

- Keep success output concise.
- On failure, report the failing test or command and the important reason.
- Separate runtime failures from packaging or installer failures.
