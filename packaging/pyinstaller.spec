# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path

from PyInstaller.utils.hooks import collect_all, copy_metadata


REPO_ROOT = Path.cwd()
ENTRYPOINT = REPO_ROOT / "scripts" / "pyinstaller_entry.py"
APP_NAME = "skb-mcp-server"

datas = []
binaries = []
hiddenimports = []

for package_name in (
    "certifi",
    "skb",
    "chromadb",
    "mcp",
    "tokenizers",
    "onnxruntime",
    "flashrank",
    "pypdf",
    "numpy",
):
    package_datas, package_binaries, package_hiddenimports = collect_all(package_name)
    datas += package_datas
    binaries += package_binaries
    hiddenimports += package_hiddenimports

for distribution_name in (
    "certifi",
    "skb-mcp-server",
    "chromadb",
    "mcp",
    "tokenizers",
    "onnxruntime",
    "flashrank",
    "pypdf",
    "numpy",
):
    try:
        datas += copy_metadata(distribution_name)
    except Exception:
        pass


a = Analysis(
    [str(ENTRYPOINT)],
    pathex=[str(REPO_ROOT)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name=APP_NAME,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    name=APP_NAME,
)
