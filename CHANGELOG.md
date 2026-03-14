# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.4] - 2026-03-14

### Changed
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
