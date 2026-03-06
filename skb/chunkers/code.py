"""Code chunker — splits on function/class boundaries via regex."""

import re
from ..config import CHUNK_SIZES, CHUNK_OVERLAPS

# Patterns for function/class boundaries per language
_BOUNDARY_PATTERNS: dict[str, list[re.Pattern]] = {
    "python": [
        re.compile(r"^(class\s+\w+|def\s+\w+|async\s+def\s+\w+)", re.MULTILINE),
    ],
    "javascript": [
        re.compile(r"^(export\s+)?(function\s+\w+|class\s+\w+|const\s+\w+\s*=)", re.MULTILINE),
    ],
    "typescript": [
        re.compile(r"^(export\s+)?(function\s+\w+|class\s+\w+|const\s+\w+\s*=|interface\s+\w+|type\s+\w+)", re.MULTILINE),
    ],
    "java": [
        re.compile(r"^\s*(public|private|protected)?\s*(static\s+)?(class|interface|enum|void|int|String|\w+)\s+\w+\s*[({]", re.MULTILINE),
    ],
    "go": [
        re.compile(r"^(func\s+|type\s+\w+\s+struct)", re.MULTILINE),
    ],
    "rust": [
        re.compile(r"^(pub\s+)?(fn\s+|struct\s+|enum\s+|impl\s+|trait\s+)", re.MULTILINE),
    ],
}

# Fallback: any language
_FALLBACK_PATTERNS = [
    re.compile(r"^(class\s+|function\s+|def\s+|fn\s+|func\s+|pub\s+fn\s+)", re.MULTILINE),
]


def chunk_code(content: str, source: str = "", **kwargs) -> list[dict]:
    """Split code into chunks at function/class boundaries."""
    chunk_size = CHUNK_SIZES["code"]
    overlap = CHUNK_OVERLAPS["code"]
    language = kwargs.get("language", "")

    text = content.strip()
    if not text:
        return []

    # If file is small enough, return as one chunk
    if len(text) <= chunk_size:
        return [{"content": text, "metadata": {"section": ""}}]

    # Try to split on function/class boundaries
    patterns = _BOUNDARY_PATTERNS.get(language, _FALLBACK_PATTERNS)
    boundaries = _find_boundaries(text, patterns)

    if len(boundaries) > 1:
        chunks = _split_at_boundaries(text, boundaries, chunk_size, overlap)
    else:
        # Fallback to line-based splitting
        chunks = _line_split(text, chunk_size, overlap)

    return [{"content": c, "metadata": {"section": ""}} for c in chunks if c.strip()]


def _find_boundaries(text: str, patterns: list[re.Pattern]) -> list[int]:
    """Find all boundary positions in text."""
    positions = {0}  # Always include start
    for pattern in patterns:
        for match in pattern.finditer(text):
            positions.add(match.start())
    return sorted(positions)


def _split_at_boundaries(
    text: str, boundaries: list[int], chunk_size: int, overlap: int
) -> list[str]:
    """Split text at the given boundary positions, merging small segments."""
    chunks = []
    current = ""

    for i, start in enumerate(boundaries):
        end = boundaries[i + 1] if i + 1 < len(boundaries) else len(text)
        segment = text[start:end]

        if len(current) + len(segment) <= chunk_size:
            current += segment
        else:
            if current:
                chunks.append(current)
            if len(segment) > chunk_size:
                # Segment itself is too large, split it
                sub = _line_split(segment, chunk_size, overlap)
                chunks.extend(sub)
                current = ""
            else:
                current = segment

    if current.strip():
        chunks.append(current)

    return chunks


def _line_split(text: str, chunk_size: int, overlap: int) -> list[str]:
    """Split text by lines, respecting chunk_size."""
    lines = text.split("\n")
    chunks = []
    current_lines: list[str] = []
    current_len = 0

    for line in lines:
        line_len = len(line) + 1  # +1 for newline
        if current_len + line_len > chunk_size and current_lines:
            chunks.append("\n".join(current_lines))
            # Keep some overlap
            overlap_lines: list[str] = []
            overlap_len = 0
            for prev_line in reversed(current_lines):
                if overlap_len + len(prev_line) + 1 > overlap:
                    break
                overlap_lines.insert(0, prev_line)
                overlap_len += len(prev_line) + 1
            current_lines = overlap_lines
            current_len = overlap_len

        current_lines.append(line)
        current_len += line_len

    if current_lines:
        chunks.append("\n".join(current_lines))

    return chunks
