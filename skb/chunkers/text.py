"""Text chunker — recursive character split at paragraph boundaries."""

from ..config import CHUNK_SIZES, CHUNK_OVERLAPS


def chunk_text(content: str, source: str = "", **kwargs) -> list[dict]:
    """Split plain text content into chunks at paragraph boundaries."""
    doc_type = kwargs.get("doc_type", "text")
    chunk_size = CHUNK_SIZES.get(doc_type, CHUNK_SIZES["text"])
    overlap = CHUNK_OVERLAPS.get(doc_type, CHUNK_OVERLAPS["text"])

    text = content.strip()
    if not text:
        return []

    # For config files (yaml, json), keep whole if small enough
    if doc_type == "config" and len(text) <= chunk_size:
        return [{"content": text, "metadata": {"section": ""}}]

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
