"""Super Knowledge Base (SKB) — local vector knowledge base for Claude Code."""

from importlib.metadata import PackageNotFoundError, version

PACKAGE_NAME = "skb-mcp-server"

try:
    __version__ = version(PACKAGE_NAME)
except PackageNotFoundError:
    __version__ = "0+unknown"
