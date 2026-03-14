---
paths:
  - ".github/**"
  - "README.md"
  - "USERGUIDE.md"
  - "CHANGELOG.md"
  - "sample/**"
  - "packaging/**"
  - "install.sh"
  - "install.ps1"
  - "uninstall.sh"
  - "uninstall.ps1"
---

# Packaging And Docs Rules

- Keep release assets, installer behavior, docs, and tests aligned.
- Do not introduce unrelated local filesystem paths into markdown files, scripts,
  templates, or examples.
- When changing release behavior, update the release workflow and the user-facing
  install instructions together.
- Keep Linux and Windows stability statements accurate if manual validation was
  not performed.
