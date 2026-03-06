"""Markdown chunker — splits on headers, falls back to recursive char split."""

import re
from ..config import CHUNK_SIZES, CHUNK_OVERLAPS


def chunk_markdown(content: str, source: str = "", **kwargs) -> list[dict]:
    """Split markdown content on headers, with fallback to char split."""
    chunk_size = CHUNK_SIZES["markdown"]
    overlap = CHUNK_OVERLAPS["markdown"]

    sections = _split_on_headers(content)

    chunks = []
    for section_title, section_body in sections:
        text = section_body.strip()
        if not text:
            continue

        if len(text) <= chunk_size:
            chunks.append({
                "content": text,
                "metadata": {"section": section_title},
            })
        else:
            # Recursively split large sections
            sub_chunks = _recursive_char_split(text, chunk_size, overlap)
            for sc in sub_chunks:
                chunks.append({
                    "content": sc,
                    "metadata": {"section": section_title},
                })

    if not chunks and content.strip():
        chunks.append({
            "content": content.strip()[:chunk_size],
            "metadata": {"section": ""},
        })

    return chunks


def _split_on_headers(text: str) -> list[tuple[str, str]]:
    """Split markdown text on ## and ### headers.

    Returns list of (header_text, body_text) tuples.
    """
    pattern = re.compile(r"^(#{1,4}\s+.+)$", re.MULTILINE)
    parts = pattern.split(text)

    sections = []
    current_header = ""

    i = 0
    while i < len(parts):
        part = parts[i]
        if pattern.match(part.strip()):
            current_header = part.strip()
            i += 1
        else:
            body = part
            if body.strip():
                sections.append((current_header, body))
            i += 1

    if not sections and text.strip():
        sections.append(("", text))

    return sections


def _recursive_char_split(text: str, chunk_size: int, overlap: int) -> list[str]:
    """Split text into chunks at paragraph boundaries, with overlap."""
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

        # Find best split point
        split_at = end
        for sep in separators:
            pos = text.rfind(sep, start, end)
            if pos > start:
                split_at = pos + len(sep)
                break

        chunks.append(text[start:split_at])
        start = max(start + 1, split_at - overlap)

    return chunks
