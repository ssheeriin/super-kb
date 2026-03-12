"""Export/import logic for SKB knowledge bases.

Two complementary approaches:
- Source-level: Portable archive of .skb/ source files (.tar.gz).
- Index-level: Export ChromaDB chunks + embeddings as gzipped JSONL (.jsonl.gz).
"""

import asyncio
import gzip
import io
import json
import logging
import os
import shutil
import sys
import tarfile
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path

from .config import SKB_FOLDER
from .store import get_all_chunks, add_documents_with_embeddings
from .sync import sync_skb_folder

logger = logging.getLogger(__name__)

EMBEDDING_MODEL = "bge-small-en-v1.5"
EMBEDDING_DIM = 384


def _to_list(obj):
    """Convert numpy arrays or other array-like objects to plain Python lists."""
    if hasattr(obj, "tolist"):
        return obj.tolist()
    return list(obj)


# ── Source-level export/import ───────────────────────────────────────────────


async def export_source(
    project_dir: str | Path,
    output_path: str = "",
    log_callback: Callable | None = None,
) -> dict:
    """Export .skb/ source files as a portable .tar.gz archive.

    Args:
        project_dir: Path to the project root containing .skb/.
        output_path: Where to write the archive. Defaults to <project_dir>/<project>-skb-source.tar.gz.
        log_callback: Optional async callable(message) for log notifications.

    Returns:
        {"archive": str, "project": str, "files": int, "size_bytes": int}
    """
    project_dir = Path(project_dir).resolve()
    skb_dir = project_dir / SKB_FOLDER
    project = project_dir.name

    if not skb_dir.is_dir():
        return {"error": f"No {SKB_FOLDER}/ folder found in {project_dir}"}

    if log_callback:
        await log_callback(f"Exporting source files for project '{project}'...")
        await asyncio.sleep(0)

    # Collect all files in .skb/ (not just supported extensions)
    files_info: list[dict] = []
    for root, _dirs, filenames in os.walk(skb_dir, followlinks=True):
        for fname in filenames:
            fpath = Path(root) / fname
            rel = fpath.relative_to(skb_dir)
            stat = fpath.stat()
            files_info.append({
                "path": str(rel),
                "abs_path": str(fpath),
                "size_bytes": stat.st_size,
                "modified_at": datetime.fromtimestamp(
                    stat.st_mtime, tz=timezone.utc
                ).isoformat(),
            })

    if not files_info:
        return {"error": f"No files found in {skb_dir}"}

    # Build manifest
    manifest = {
        "version": 1,
        "type": "source",
        "project": project,
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "file_count": len(files_info),
        "files": [
            {"path": f["path"], "size_bytes": f["size_bytes"], "modified_at": f["modified_at"]}
            for f in files_info
        ],
    }

    # Determine output path
    if not output_path:
        output_path = str(project_dir / f"{project}-skb-source.tar.gz")

    if log_callback:
        await log_callback(f"Creating archive with {len(files_info)} files...")
        await asyncio.sleep(0)

    # Create tar.gz archive
    with tarfile.open(output_path, "w:gz") as tar:
        # Add manifest
        manifest_bytes = json.dumps(manifest, indent=2).encode("utf-8")
        info = tarfile.TarInfo(name="manifest.json")
        info.size = len(manifest_bytes)
        tar.addfile(info, io.BytesIO(manifest_bytes))

        # Add files under skb/ prefix
        for f in files_info:
            arcname = f"skb/{f['path']}"
            tar.add(f["abs_path"], arcname=arcname)

    archive_size = Path(output_path).stat().st_size

    if log_callback:
        await log_callback(f"Exported {len(files_info)} files to {output_path} ({archive_size} bytes)")
        await asyncio.sleep(0)

    return {
        "archive": output_path,
        "project": project,
        "files": len(files_info),
        "size_bytes": archive_size,
    }


async def import_source(
    archive_path: str | Path,
    project_dir: str | Path = "",
    merge: bool = True,
    run_sync: bool = True,
    log_callback: Callable | None = None,
    progress_callback: Callable | None = None,
) -> dict:
    """Import a source archive into a project's .skb/ folder.

    Args:
        archive_path: Path to the .tar.gz archive.
        project_dir: Target project root. If empty, uses the project name from manifest.
        merge: If True, merge with existing files. If False, wipe .skb/ first.
        run_sync: If True, run sync_skb_folder() after extraction.
        log_callback: Optional async callable(message) for log notifications.
        progress_callback: Optional async callable(current, total) for progress.

    Returns:
        {"project": str, "files_imported": int, "sync_result": dict|None}
    """
    archive_path = Path(archive_path).resolve()
    if not archive_path.exists():
        return {"error": f"Archive not found: {archive_path}"}

    if log_callback:
        await log_callback(f"Reading archive {archive_path}...")
        await asyncio.sleep(0)

    # Validate and extract
    with tarfile.open(str(archive_path), "r:gz") as tar:
        # Security: reject dangerous entries
        try:
            _validate_tar_safety(tar)
        except ValueError as e:
            return {"error": str(e)}

        # Read manifest
        try:
            manifest_member = tar.getmember("manifest.json")
            manifest_f = tar.extractfile(manifest_member)
            if manifest_f is None:
                return {"error": "Cannot read manifest.json from archive"}
            manifest = json.loads(manifest_f.read().decode("utf-8"))
        except KeyError:
            return {"error": "Archive missing manifest.json — not a valid SKB source archive"}

        # Validate manifest
        if manifest.get("version") != 1 or manifest.get("type") != "source":
            return {"error": f"Invalid manifest: expected version=1, type=source, got version={manifest.get('version')}, type={manifest.get('type')}"}

        project = manifest.get("project", "unknown")

        # Determine target directory
        if project_dir:
            project_dir = Path(project_dir).resolve()
        else:
            project_dir = Path.cwd()

        skb_dir = project_dir / SKB_FOLDER

        if log_callback:
            await log_callback(f"Importing into {skb_dir} (merge={merge})...")
            await asyncio.sleep(0)

        # Wipe if not merging
        if not merge and skb_dir.exists():
            shutil.rmtree(skb_dir)

        skb_dir.mkdir(parents=True, exist_ok=True)

        # Extract files from skb/ prefix
        files_imported = 0
        members = [m for m in tar.getmembers() if m.name.startswith("skb/") and m.isfile()]
        total = len(members)

        for i, member in enumerate(members, start=1):
            # Strip skb/ prefix
            rel_path = member.name[len("skb/"):]
            target = skb_dir / rel_path
            target.parent.mkdir(parents=True, exist_ok=True)

            source_f = tar.extractfile(member)
            if source_f is not None:
                target.write_bytes(source_f.read())
                files_imported += 1

            if progress_callback:
                await progress_callback(i, total)
                await asyncio.sleep(0)

    if log_callback:
        await log_callback(f"Extracted {files_imported} files into {skb_dir}")
        await asyncio.sleep(0)

    # Run sync if requested
    sync_result = None
    if run_sync:
        if log_callback:
            await log_callback("Running sync to rebuild index...")
            await asyncio.sleep(0)
        sync_result = await sync_skb_folder(
            project_dir, progress_callback=progress_callback, log_callback=log_callback
        )

    return {
        "project": project,
        "files_imported": files_imported,
        "sync_result": sync_result,
    }


def _validate_tar_safety(tar: tarfile.TarFile) -> None:
    """Reject tar archives with path traversal or absolute paths."""
    # Python 3.12+ has tarfile.data_filter
    if sys.version_info >= (3, 12):
        # Validate all members using the safe data_filter
        for member in tar.getmembers():
            try:
                tarfile.data_filter(member, "/tmp/skb-validate")
            except (tarfile.AbsolutePathError, tarfile.OutsideDestinationError) as e:
                raise ValueError(f"Unsafe archive entry rejected: {e}") from e
    else:
        # Manual validation for older Python
        for member in tar.getmembers():
            if member.name.startswith("/") or ".." in member.name.split("/"):
                raise ValueError(
                    f"Unsafe archive entry rejected: {member.name} "
                    "(absolute path or path traversal detected)"
                )


# ── Index-level export/import ────────────────────────────────────────────────


async def export_index(
    project: str,
    output_path: str = "",
    log_callback: Callable | None = None,
) -> dict:
    """Export vector index as gzipped JSONL.

    Args:
        project: Project name in ChromaDB.
        output_path: Where to write the archive. Defaults to <cwd>/<project>-skb-index.jsonl.gz.
        log_callback: Optional async callable(message) for log notifications.

    Returns:
        {"archive": str, "project": str, "chunks": int, "size_bytes": int}
    """
    if log_callback:
        await log_callback(f"Retrieving chunks for project '{project}'...")
        await asyncio.sleep(0)

    data = get_all_chunks(project)
    chunk_count = len(data["ids"])

    if chunk_count == 0:
        return {"error": f"No chunks found for project '{project}'"}

    # Strip machine-specific metadata
    cleaned_metadatas = []
    for meta in data["metadatas"]:
        cleaned = {k: v for k, v in meta.items() if k != "source_abs"}
        cleaned_metadatas.append(cleaned)

    if not output_path:
        output_path = str(Path.cwd() / f"{project}-skb-index.jsonl.gz")

    if log_callback:
        await log_callback(f"Writing {chunk_count} chunks to {output_path}...")
        await asyncio.sleep(0)

    # Write gzipped JSONL
    header = {
        "version": 1,
        "type": "index",
        "project": project,
        "model": EMBEDDING_MODEL,
        "embedding_dim": EMBEDDING_DIM,
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "chunk_count": chunk_count,
    }

    with gzip.open(output_path, "wt", encoding="utf-8") as f:
        f.write(json.dumps(header) + "\n")
        for i in range(chunk_count):
            record = {
                "id": data["ids"][i],
                "document": data["documents"][i],
                "metadata": cleaned_metadatas[i],
                "embedding": _to_list(data["embeddings"][i]),
            }
            f.write(json.dumps(record) + "\n")

    archive_size = Path(output_path).stat().st_size

    if log_callback:
        await log_callback(f"Exported {chunk_count} chunks to {output_path} ({archive_size} bytes)")
        await asyncio.sleep(0)

    return {
        "archive": output_path,
        "project": project,
        "chunks": chunk_count,
        "size_bytes": archive_size,
    }


async def import_index(
    archive_path: str | Path,
    project: str = "",
    log_callback: Callable | None = None,
    progress_callback: Callable | None = None,
) -> dict:
    """Import a gzipped JSONL index archive into ChromaDB.

    Args:
        archive_path: Path to the .jsonl.gz archive.
        project: Target project name. If empty, uses the project from the header.
        log_callback: Optional async callable(message) for log notifications.
        progress_callback: Optional async callable(current, total) for progress.

    Returns:
        {"project": str, "chunks_imported": int, "model_match": bool}
    """
    archive_path = Path(archive_path).resolve()
    if not archive_path.exists():
        return {"error": f"Archive not found: {archive_path}"}

    if log_callback:
        await log_callback(f"Reading index archive {archive_path}...")
        await asyncio.sleep(0)

    with gzip.open(str(archive_path), "rt", encoding="utf-8") as f:
        # Read header
        header_line = f.readline()
        if not header_line:
            return {"error": "Empty archive"}

        header = json.loads(header_line)

        # Validate header
        if header.get("version") != 1 or header.get("type") != "index":
            return {"error": f"Invalid header: expected version=1, type=index, got version={header.get('version')}, type={header.get('type')}"}

        if header.get("embedding_dim") != EMBEDDING_DIM:
            return {"error": f"Embedding dimension mismatch: archive has {header.get('embedding_dim')}, expected {EMBEDDING_DIM}. Cannot import."}

        model_match = header.get("model") == EMBEDDING_MODEL
        if not model_match and log_callback:
            await log_callback(
                f"WARNING: Model mismatch — archive uses '{header.get('model')}', "
                f"current model is '{EMBEDDING_MODEL}'. Proceeding anyway."
            )
            await asyncio.sleep(0)

        target_project = project or header.get("project", "unknown")
        total_chunks = header.get("chunk_count", 0)

        if log_callback:
            await log_callback(f"Importing {total_chunks} chunks into project '{target_project}'...")
            await asyncio.sleep(0)

        # Read and batch-upsert chunks
        batch_size = 500
        ids: list[str] = []
        documents: list[str] = []
        metadatas: list[dict] = []
        embeddings: list[list[float]] = []
        chunks_imported = 0

        for line in f:
            line = line.strip()
            if not line:
                continue

            record = json.loads(line)
            ids.append(record["id"])
            documents.append(record["document"])
            meta = record["metadata"]
            # ChromaDB requires non-empty metadata dicts
            if not meta:
                meta = {"_imported": "true"}
            metadatas.append(meta)
            embeddings.append(record["embedding"])

            if len(ids) >= batch_size:
                add_documents_with_embeddings(
                    target_project, ids, documents, metadatas, embeddings
                )
                chunks_imported += len(ids)
                if progress_callback:
                    await progress_callback(chunks_imported, total_chunks)
                    await asyncio.sleep(0)
                if log_callback:
                    await log_callback(f"Imported {chunks_imported}/{total_chunks} chunks...")
                    await asyncio.sleep(0)
                ids, documents, metadatas, embeddings = [], [], [], []

        # Flush remaining
        if ids:
            add_documents_with_embeddings(
                target_project, ids, documents, metadatas, embeddings
            )
            chunks_imported += len(ids)

    if log_callback:
        await log_callback(f"Import complete: {chunks_imported} chunks into '{target_project}'")
        await asyncio.sleep(0)

    return {
        "project": target_project,
        "chunks_imported": chunks_imported,
        "model_match": model_match,
    }
