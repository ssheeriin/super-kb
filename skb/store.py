"""ChromaDB wrapper — create/get collections, add, query, delete, list."""

import logging

import chromadb
from chromadb.config import Settings

from .config import CHROMADB_DIR

logger = logging.getLogger(__name__)

# Module-level client (lazy init)
_client: chromadb.ClientAPI | None = None


def _get_client() -> chromadb.ClientAPI:
    """Get or create the persistent ChromaDB client."""
    global _client
    if _client is None:
        CHROMADB_DIR.mkdir(parents=True, exist_ok=True)
        _client = chromadb.PersistentClient(
            path=str(CHROMADB_DIR),
            settings=Settings(anonymized_telemetry=False),
        )
    return _client


def get_or_create_collection(project: str) -> chromadb.Collection:
    """Get or create a collection for the given project name."""
    client = _get_client()
    safe_name = _sanitize_collection_name(project)
    return client.get_or_create_collection(
        name=safe_name,
        metadata={"hnsw:space": "cosine"},
    )


def add_documents(
    project: str,
    ids: list[str],
    documents: list[str],
    metadatas: list[dict],
) -> None:
    """Upsert documents into a project's collection."""
    collection = get_or_create_collection(project)
    collection.upsert(ids=ids, documents=documents, metadatas=metadatas)


def query_collection(
    project: str,
    query_text: str,
    n_results: int = 5,
    where: dict | None = None,
) -> list[dict]:
    """Query a project's collection. Returns list of result dicts."""
    collection = get_or_create_collection(project)
    if collection.count() == 0:
        return []

    kwargs: dict = {
        "query_texts": [query_text],
        "n_results": min(n_results, collection.count()),
    }
    if where:
        kwargs["where"] = where

    results = collection.query(**kwargs)

    out = []
    for i in range(len(results["ids"][0])):
        meta = results["metadatas"][0][i] if results["metadatas"] else {}
        out.append({
            "content": results["documents"][0][i] if results["documents"] else "",
            "score": 1.0 - (results["distances"][0][i] if results["distances"] else 0),
            "source_file": meta.get("source", ""),
            "project": meta.get("project", project),
            "doc_type": meta.get("doc_type", ""),
            "section": meta.get("section", ""),
            "language": meta.get("language"),
        })
    return out


def query_multiple_collections(
    query_text: str,
    n_results: int = 5,
    where: dict | None = None,
) -> list[dict]:
    """Query all collections and merge results by score."""
    client = _get_client()
    all_results = []
    for col_info in client.list_collections():
        col_name = col_info if isinstance(col_info, str) else col_info.name
        try:
            results = query_collection(col_name, query_text, n_results, where)
            all_results.extend(results)
        except Exception:
            continue

    all_results.sort(key=lambda r: r["score"], reverse=True)
    return all_results[:n_results]


def delete_by_source(project: str, source: str) -> None:
    """Delete all chunks from a specific source file."""
    collection = get_or_create_collection(project)
    try:
        collection.delete(where={"source": source})
    except Exception:
        pass


def delete_collection(project: str) -> bool:
    """Delete an entire project collection. Returns True if it existed."""
    client = _get_client()
    safe_name = _sanitize_collection_name(project)
    try:
        client.delete_collection(name=safe_name)
        return True
    except Exception:
        return False


def list_collections() -> list[dict]:
    """List all collections with counts."""
    client = _get_client()
    result = []
    for col_info in client.list_collections():
        col_name = col_info if isinstance(col_info, str) else col_info.name
        col = client.get_collection(name=col_name)
        result.append({
            "project": col_name,
            "chunk_count": col.count(),
        })
    return result


def list_documents_in_collection(project: str) -> list[dict]:
    """List unique source files in a project collection with metadata."""
    collection = get_or_create_collection(project)
    count = collection.count()
    if count == 0:
        return []

    all_data = collection.get(include=["metadatas"])
    sources: dict[str, dict] = {}
    for meta in all_data["metadatas"]:
        src = meta.get("source", "unknown")
        if src not in sources:
            sources[src] = {
                "source": src,
                "doc_type": meta.get("doc_type", ""),
                "chunk_count": 0,
                "ingested_at": meta.get("ingested_at", ""),
                "file_modified_at": meta.get("file_modified_at", ""),
            }
        sources[src]["chunk_count"] += 1
    return list(sources.values())


def get_project_dir(project: str) -> str | None:
    """Derive the project directory from stored chunk metadata.

    Returns the absolute project directory path, or None if the collection
    is empty or the path cannot be determined.
    """
    collection = get_or_create_collection(project)
    if collection.count() == 0:
        return None

    sample = collection.peek(limit=1)
    if not sample["metadatas"]:
        return None

    meta = sample["metadatas"][0]
    source_abs = meta.get("source_abs", "")
    source = meta.get("source", "")

    if not source_abs or not source:
        return None

    # project_dir = source_abs minus the relative source suffix
    if source_abs.endswith(source):
        project_dir = source_abs[: -len(source)].rstrip("/")
        return project_dir

    return None


def warm_up() -> None:
    """Trigger ChromaDB's lazy ONNX embedding model load.

    Creates a temporary collection, upserts a dummy document (which forces
    the embedding model to load), then deletes the collection.
    """
    logger.info("Warming up ChromaDB embedding model...")
    client = _get_client()
    tmp_name = "skb-warmup-tmp"
    col = client.get_or_create_collection(name=tmp_name)
    col.upsert(ids=["warmup"], documents=["warmup"])
    client.delete_collection(name=tmp_name)
    logger.info("ChromaDB embedding model ready.")


def _sanitize_collection_name(name: str) -> str:
    """Sanitize a project name for use as a ChromaDB collection name.

    ChromaDB requires: 3-63 chars, starts/ends with alphanumeric,
    only alphanumeric, underscore, hyphen allowed.
    """
    import re
    # Replace any non-alphanumeric chars (except hyphen/underscore) with hyphen
    sanitized = re.sub(r"[^a-zA-Z0-9_-]", "-", name)
    # Strip leading/trailing non-alphanumeric
    sanitized = re.sub(r"^[^a-zA-Z0-9]+", "", sanitized)
    sanitized = re.sub(r"[^a-zA-Z0-9]+$", "", sanitized)
    # Ensure minimum length
    if len(sanitized) < 3:
        sanitized = sanitized + "___"[:3 - len(sanitized)]
    # Truncate to max length
    if len(sanitized) > 63:
        sanitized = sanitized[:63]
        sanitized = re.sub(r"[^a-zA-Z0-9]+$", "", sanitized)
    return sanitized or "default"
