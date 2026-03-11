""".skb/ folder scanner and incremental sync logic."""

import asyncio
import hashlib
import logging
import os
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path

from .config import SKB_FOLDER, EXTENSION_MAP
from .ingest import ingest_file
from .store import (
    delete_by_source,
    delete_collection,
    list_documents_in_collection,
)

logger = logging.getLogger(__name__)


async def sync_skb_folder(
    project_dir: str | Path,
    progress_callback: Callable | None = None,
    log_callback: Callable | None = None,
) -> dict:
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
    logger.info("Sync started for project '%s' (%s)", project, skb_dir)

    # Discover all supported files in .skb/
    disk_files = _scan_skb_files(skb_dir)
    total = len(disk_files)

    # Get currently indexed files
    indexed_docs = list_documents_in_collection(project)
    indexed_map = {doc["source"]: doc for doc in indexed_docs}

    if progress_callback:
        await progress_callback(0, total)
        await asyncio.sleep(0)
    if log_callback:
        await log_callback(f"Syncing {total} files for project '{project}'")
        await asyncio.sleep(0)

    files_added = 0
    files_updated = 0
    files_removed = 0
    files_failed = 0
    total_chunks = 0

    # Process each file on disk
    processed_sources = set()
    for i, file_path in enumerate(disk_files, start=1):
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
                logger.info("[%d/%d] Unchanged: %s", i, total, relative_path)
            else:
                # Modified — delete old chunks, re-ingest
                delete_by_source(project, relative_path)
                try:
                    chunks = ingest_file(file_path, project, skb_dir)
                    total_chunks += chunks
                    files_updated += 1
                    logger.info("[%d/%d] Updated (%d chunks): %s", i, total, chunks, relative_path)
                except Exception:
                    files_failed += 1
                    logger.warning("[%d/%d] Failed to ingest (update): %s", i, total, relative_path, exc_info=True)
        else:
            # New file
            try:
                chunks = ingest_file(file_path, project, skb_dir)
                total_chunks += chunks
                files_added += 1
                logger.info("[%d/%d] Added (%d chunks): %s", i, total, chunks, relative_path)
            except Exception:
                files_failed += 1
                logger.warning("[%d/%d] Failed to ingest (add): %s", i, total, relative_path, exc_info=True)

        if progress_callback:
            await progress_callback(i, total)
            await asyncio.sleep(0)
        if log_callback:
            await log_callback(f"[{i}/{total}] {file_path.name}")
            await asyncio.sleep(0)

    # Remove chunks for files that no longer exist on disk
    for source, doc in indexed_map.items():
        if source not in processed_sources:
            delete_by_source(project, source)
            files_removed += 1
            logger.info("Removed (deleted from disk): %s", source)

    logger.info(
        "Sync complete for '%s': +%d added, ~%d updated, -%d removed, !%d failed, %d total chunks",
        project, files_added, files_updated, files_removed, files_failed, total_chunks,
    )

    return {
        "project": project,
        "files_added": files_added,
        "files_updated": files_updated,
        "files_removed": files_removed,
        "files_failed": files_failed,
        "total_chunks": total_chunks,
    }


def _scan_skb_files(skb_dir: Path) -> list[Path]:
    """Recursively find all supported files in the .skb/ directory.

    Uses os.walk with followlinks=True so that symlinked directories
    are traversed (Path.rglob does not follow symlinks by default).
    """
    files = []
    for root, _dirs, filenames in os.walk(skb_dir, followlinks=True):
        for fname in filenames:
            path = Path(root) / fname
            if path.suffix.lower() in EXTENSION_MAP:
                files.append(path)
    return sorted(files)


def _file_fingerprint(file_path: Path) -> str:
    """Create a fingerprint from file path and modification time."""
    mtime = str(file_path.stat().st_mtime)
    raw = f"{file_path}:{mtime}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


async def reindex_project(
    project_dir: str | Path,
    progress_callback: Callable | None = None,
    log_callback: Callable | None = None,
) -> dict:
    """Delete all indexed data for a project and rebuild from scratch.

    Returns the sync result dict with an extra ``reindexed: True`` key.
    """
    project_dir = Path(project_dir).resolve()
    project = project_dir.name

    logger.info("Reindex requested for project '%s' — deleting collection", project)
    if log_callback:
        await log_callback(f"Deleting index for project '{project}'...")
        await asyncio.sleep(0)
    delete_collection(project)

    result = await sync_skb_folder(project_dir, progress_callback=progress_callback, log_callback=log_callback)
    result["reindexed"] = True
    return result
