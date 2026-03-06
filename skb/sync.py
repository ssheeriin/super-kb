""".skb/ folder scanner and incremental sync logic."""

import hashlib
from datetime import datetime, timezone
from pathlib import Path

from .config import SKB_FOLDER, EXTENSION_MAP
from .ingest import ingest_file
from .store import (
    delete_by_source,
    get_or_create_collection,
    list_documents_in_collection,
)


def sync_skb_folder(project_dir: str | Path) -> dict:
    """Scan the .skb/ folder in project_dir and sync to vector store.

    Returns a summary dict with counts of files added, updated, removed.
    """
    project_dir = Path(project_dir).resolve()
    skb_dir = project_dir / SKB_FOLDER

    if not skb_dir.is_dir():
        return {
            "project": project_dir.name,
            "error": f"No {SKB_FOLDER}/ folder found in {project_dir}",
            "files_added": 0,
            "files_updated": 0,
            "files_removed": 0,
            "total_chunks": 0,
        }

    project = project_dir.name

    # Discover all supported files in .skb/
    disk_files = _scan_skb_files(skb_dir)

    # Get currently indexed files
    indexed_docs = list_documents_in_collection(project)
    indexed_map = {doc["source"]: doc for doc in indexed_docs}

    files_added = 0
    files_updated = 0
    files_removed = 0
    total_chunks = 0

    # Process each file on disk
    processed_sources = set()
    for file_path in disk_files:
        relative_path = str(file_path.relative_to(project_dir))
        processed_sources.add(relative_path)

        file_fingerprint = _file_fingerprint(file_path)

        if relative_path in indexed_map:
            # Check if modified
            stored_mtime = indexed_map[relative_path].get("file_modified_at", "")
            current_mtime = datetime.fromtimestamp(
                file_path.stat().st_mtime, tz=timezone.utc
            ).isoformat()

            if stored_mtime == current_mtime:
                # Unchanged — skip
                total_chunks += indexed_map[relative_path].get("chunk_count", 0)
                continue
            else:
                # Modified — delete old chunks, re-ingest
                delete_by_source(project, relative_path)
                chunks = ingest_file(file_path, project, skb_dir)
                total_chunks += chunks
                files_updated += 1
        else:
            # New file
            chunks = ingest_file(file_path, project, skb_dir)
            total_chunks += chunks
            files_added += 1

    # Remove chunks for files that no longer exist on disk
    for source, doc in indexed_map.items():
        if source not in processed_sources:
            delete_by_source(project, source)
            files_removed += 1

    return {
        "project": project,
        "files_added": files_added,
        "files_updated": files_updated,
        "files_removed": files_removed,
        "total_chunks": total_chunks,
    }


def _scan_skb_files(skb_dir: Path) -> list[Path]:
    """Recursively find all supported files in the .skb/ directory."""
    files = []
    for path in skb_dir.rglob("*"):
        if path.is_file() and path.suffix.lower() in EXTENSION_MAP:
            files.append(path)
    return sorted(files)


def _file_fingerprint(file_path: Path) -> str:
    """Create a fingerprint from file path and modification time."""
    mtime = str(file_path.stat().st_mtime)
    raw = f"{file_path}:{mtime}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]
