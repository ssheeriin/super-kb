"""Configuration constants for the SKB MCP server."""

from pathlib import Path

# ── Paths ───────────────────────────────────────────────────────────────────
SKB_ROOT = Path(__file__).resolve().parent.parent  # ~/temp/skb/
CHROMADB_DIR = SKB_ROOT / "chromadb"

# ── .skb/ folder name ──────────────────────────────────────────────────────
SKB_FOLDER = ".skb"

# ── Supported file extensions → doc_type mapping ──────────────────────────
EXTENSION_MAP: dict[str, str] = {
    ".md": "markdown",
    ".txt": "text",
    ".rst": "text",
    ".pdf": "pdf",
    ".py": "code",
    ".js": "code",
    ".ts": "code",
    ".java": "code",
    ".go": "code",
    ".rs": "code",
    ".yaml": "config",
    ".yml": "config",
    ".json": "config",
}

# ── Language detection from extension ─────────────────────────────────────
LANGUAGE_MAP: dict[str, str] = {
    ".py": "python",
    ".js": "javascript",
    ".ts": "typescript",
    ".java": "java",
    ".go": "go",
    ".rs": "rust",
}

# ── Chunking parameters ──────────────────────────────────────────────────
CHUNK_SIZES: dict[str, int] = {
    "markdown": 1000,
    "text": 1000,
    "pdf": 1000,
    "code": 1500,
    "config": 3000,
}

CHUNK_OVERLAPS: dict[str, int] = {
    "markdown": 200,
    "text": 200,
    "pdf": 200,
    "code": 200,
    "config": 0,
}
