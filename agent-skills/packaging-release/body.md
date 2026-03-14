# Packaging Release

Use this skill when the task involves release automation, standalone binaries,
wheel packaging, installer scripts, uninstall scripts, or GitHub release assets.

## Primary Files

- `pyproject.toml`
- `install.sh`
- `install.ps1`
- `uninstall.sh`
- `uninstall.ps1`
- `.github/workflows/release.yml`
- `packaging/`
- `scripts/`
- `tests/test_build_install.py`
- `tests/test_uninstall_scripts.py`

## Workflow

1. Identify whether the change affects:
   - Python package install
   - standalone binary packaging
   - release asset naming
   - installer or uninstaller behavior
   - versioning and release automation
2. Keep scripts, tests, and docs aligned.
3. Prefer changes that preserve a clean copy-paste install flow.

## Output

- Be explicit about platform coverage.
- If a platform was only exercised in CI, say so.
