"""Configuration constants for the SKB MCP server."""

import os
from pathlib import Path

# ── Paths ───────────────────────────────────────────────────────────────────
SKB_HOME = Path(os.environ.get("SKB_HOME", Path.home() / ".skb"))
CHROMADB_DIR = SKB_HOME / "chromadb"

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

# ── Safety limits ────────────────────────────────────────────────────────
MAX_PDF_PAGES = 200
MAX_CONTENT_CHARS = 500_000

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

# ── Reranker (FlashRank) ────────────────────────────────────────────────
RERANK_ENABLED: bool = os.environ.get("SKB_RERANK_ENABLED", "true").lower() in ("true", "1", "yes")
RERANK_MODEL: str = os.environ.get("SKB_RERANK_MODEL", "ms-marco-TinyBERT-L-2-v2")
RERANK_MAX_LENGTH: int = int(os.environ.get("SKB_RERANK_MAX_LENGTH", "512"))
RERANK_RETRIEVAL_MULTIPLIER: int = int(os.environ.get("SKB_RERANK_RETRIEVAL_MULTIPLIER", "3"))
