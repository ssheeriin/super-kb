"""PDF chunker — extract text via pypdf, then recursive char split."""

from ..config import CHUNK_SIZES, CHUNK_OVERLAPS


def chunk_pdf(content: str, source: str = "", **kwargs) -> list[dict]:
    """Split PDF-extracted text into chunks.

    Note: content here is already extracted text (extraction happens in ingest.py).
    We split on page markers if present, then recursive char split.
    """
    chunk_size = CHUNK_SIZES["pdf"]
    overlap = CHUNK_OVERLAPS["pdf"]

    text = content.strip()
    if not text:
        return []

    if len(text) <= chunk_size:
        return [{"content": text, "metadata": {"section": ""}}]

    # Split into chunks
    chunks = _recursive_split(text, chunk_size, overlap)
    return [{"content": c, "metadata": {"section": ""}} for c in chunks]


def _recursive_split(text: str, chunk_size: int, overlap: int) -> list[str]:
    """Split text into chunks with overlap at natural boundaries."""
    if len(text) <= chunk_size:
        return [text]

    separators = ["\n\n", "\n", ". ", " "]
    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size

        if end >= len(text):
            chunks.append(text[start:])
            break

        split_at = end
        for sep in separators:
            pos = text.rfind(sep, start, end)
            if pos > start:
                split_at = pos + len(sep)
                break

        chunks.append(text[start:split_at])
        start = max(start + 1, split_at - overlap)

    return chunks
