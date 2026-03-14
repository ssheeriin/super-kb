# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.9] - 2026-03-13

### Added
- Cross-tool agentic-coding scaffolding with shared `AGENTS.md` rules, a Claude adapter, Cline rules, and portable skills generated for Claude, Codex, and Cline.

### Changed
- Fixed the packaged `skb-mcp-server` no-argument path so interactive invocations reliably print usage instead of starting and hanging as an MCP server.

## [0.2.8] - 2026-03-14

### Added
- `uninstall.sh` and `uninstall.ps1` for removing the machine-level install and optional cache/project MCP state.
- `skb-mcp-server remove-mcp-config` for cleaning up project-scoped `.mcp.json` entries.

### Changed
- The installer now writes a user-scoped install manifest so uninstall can remove the exact installed paths more safely.
- `skb-mcp-server` now prints usage in an interactive terminal when run without arguments, while still starting the MCP server for non-interactive stdio launches.

## [0.2.7] - 2026-03-14

### Changed
- Fixed packaged-model downloads by using an explicit `certifi` CA bundle in the embedded downloader.
- Added coverage for the CA-bundle download path used by the standalone release artifacts.

## [0.2.6] - 2026-03-14

### Changed
- Made MCP server startup lazy so first-time Claude registration does not block on model download or warm-up.
- Updated installer-driven Claude registration to use the absolute installed executable path.

## [0.2.5] - 2026-03-14

### Changed
- Fixed the standalone release workflow after an invalid matrix entry blocked tag-based releases.
- Switched the Intel macOS standalone build to GitHub's supported `macos-15-intel` runner label for public repositories.

## [0.2.3] - 2026-03-14

### Added
- Standalone installer scripts for macOS/Linux and Windows.
- Project-scoped `.mcp.json` generation for team-owned repositories.
- CLI commands for diagnostics, version reporting, and model bootstrap.
- Open-source community files and GitHub templates.

### Changed
- Added explicit release notes and installer warnings that Linux and Windows standalone bundles are alpha.
- Simplified the alternative wheel install command to use the stable latest-release alias.

## [0.2.2] - 2026-03-13

### Changed
- Added a stable release-wheel alias for simpler install commands.
- Improved release automation and documentation.

## [0.2.1] - 2026-03-13

### Changed
- Refined release packaging and install behavior.

## [0.2.0] - 2026-03-13

### Added
- Standalone package entrypoint under `skb/`.
- Integration coverage for provisioning, indexing, search, and install flows.
