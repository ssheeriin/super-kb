"""Document processing pipeline — read file, detect type, chunk, attach metadata, upsert."""

import hashlib
from datetime import datetime, timezone
from pathlib import Path

from .config import EXTENSION_MAP, LANGUAGE_MAP
from .chunkers import chunk_document
from .store import add_documents


def ingest_file(
    file_path: Path,
    project: str,
    skb_dir: Path,
) -> int:
    """Ingest a single file into the vector store.

    Returns the number of chunks created.
    """
    ext = file_path.suffix.lower()
    doc_type = EXTENSION_MAP.get(ext)
    if doc_type is None:
        return 0

    # Extract text content
    content = _extract_content(file_path, doc_type)
    if not content or not content.strip():
        return 0

    # Relative path within project (relative to .skb/ parent)
    relative_path = str(file_path.relative_to(skb_dir.parent))
    language = LANGUAGE_MAP.get(ext)

    # Chunk the document
    chunks = chunk_document(
        content,
        doc_type=doc_type,
        source=relative_path,
        language=language,
    )

    if not chunks:
        return 0

    # Build IDs, documents, and metadata lists for upsert
    now = datetime.now(timezone.utc).isoformat()
    file_mtime = datetime.fromtimestamp(
        file_path.stat().st_mtime, tz=timezone.utc
    ).isoformat()

    ids = []
    documents = []
    metadatas = []

    for i, chunk in enumerate(chunks):
        chunk_id = _make_chunk_id(project, relative_path, i)
        ids.append(chunk_id)
        documents.append(chunk["content"])

        meta = {
            "source": relative_path,
            "source_abs": str(file_path),
            "project": project,
            "doc_type": doc_type,
            "section": chunk.get("metadata", {}).get("section", ""),
            "chunk_index": i,
            "total_chunks": len(chunks),
            "ingested_at": now,
            "file_modified_at": file_mtime,
        }
        if language:
            meta["language"] = language
        metadatas.append(meta)

    add_documents(project, ids, documents, metadatas)
    return len(chunks)


def _extract_content(file_path: Path, doc_type: str) -> str:
    """Extract text content from a file based on its type."""
    if doc_type == "pdf":
        return _extract_pdf(file_path)
    else:
        return file_path.read_text(encoding="utf-8", errors="replace")


def _extract_pdf(file_path: Path) -> str:
    """Extract text from a PDF using pypdf."""
    try:
        from pypdf import PdfReader
        reader = PdfReader(str(file_path))
        pages = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                pages.append(text)
        return "\n\n".join(pages)
    except Exception as e:
        return f"[PDF extraction failed: {e}]"


def _make_chunk_id(project: str, relative_path: str, chunk_index: int) -> str:
    """Generate a deterministic chunk ID."""
    raw = f"{project}:{relative_path}:{chunk_index}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]
