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
    # Minimum forward progress per iteration to prevent micro-chunk crawl.
    # Without this, overlap can cause start to barely advance when a separator
    # is found near the beginning of the chunk window, producing hundreds of
    # nearly-identical chunks (e.g., when a long URL sits before a \n\n).
    min_advance = max(chunk_size // 2, 1)
    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size

        if end >= len(text):
            chunks.append(text[start:])
            break

        # Find the best separator to split at
        split_at = None
        for sep in separators:
            pos = text.rfind(sep, start, end)
            if pos > start:
                split_at = pos + len(sep)
                break

        if split_at is not None:
            chunks.append(text[start:split_at])
            # Apply overlap but guarantee meaningful forward progress
            start = max(start + min_advance, split_at - overlap)
        else:
            # No separator found — hard split, no overlap
            chunks.append(text[start:end])
            start = end

    return chunks
