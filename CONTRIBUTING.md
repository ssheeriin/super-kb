# Contributing

Thanks for contributing to SKB.

## Before You Start

- Open an issue for significant changes before starting work.
- Keep changes focused. Large mixed PRs are harder to review and release.
- Follow the repository's documented install and test workflows.

## Development Setup

Source-checkout workflow:

```bash
git clone https://github.com/ssheeriin/super-kb.git
cd super-kb
uv run --with pytest --with build pytest -q
```

Run the server locally:

```bash
uv --directory /path/to/super-kb run python -m skb
```

## What Good Contributions Look Like

- Bug fixes include a regression test when practical.
- New features include documentation updates.
- Public CLI changes update `README.md` and `USERGUIDE.md`.
- GitHub release or install changes are validated with a clean-room flow.

## Pull Request Checklist

Before opening a PR:

- Run:

```bash
python3 -m py_compile skb/*.py skb/chunkers/*.py tests/*.py scripts/*.py
uv run --with pytest --with build pytest -q
```

- If you changed packaging or installer behavior, validate one install path end to end.
- Keep commit history readable. Squash fixup noise before merge if needed.

## Scope Boundaries

- Avoid unrelated formatting-only edits in functional PRs.
- Do not commit local IDE, cache, or generated binary artifacts.
- Do not change the project license or governance files casually.

## Reporting Problems

- Security issues: follow [SECURITY.md](SECURITY.md).
- Bugs and feature requests: use the GitHub issue templates.
- Usage questions: see [SUPPORT.md](SUPPORT.md).
