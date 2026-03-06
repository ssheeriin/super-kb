"""Chunker dispatcher — picks the right chunker based on file type."""

from .markdown import chunk_markdown
from .text import chunk_text
from .code import chunk_code
from .pdf import chunk_pdf

# Map doc_type to chunker function
CHUNKERS = {
    "markdown": chunk_markdown,
    "text": chunk_text,
    "code": chunk_code,
    "pdf": chunk_pdf,
    "config": chunk_text,  # configs use text chunker (usually small, kept whole)
}


def chunk_document(content: str, doc_type: str, source: str, **kwargs) -> list[dict]:
    """Dispatch to the appropriate chunker based on doc_type.

    Returns a list of dicts: [{"content": str, "metadata": dict}, ...]
    """
    chunker = CHUNKERS.get(doc_type, chunk_text)
    return chunker(content, source=source, **kwargs)
