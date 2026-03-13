"""MCP tool definitions for the SKB server."""

from collections.abc import Callable
from pathlib import Path
from urllib.parse import unquote

from .provisioning import provision_project
from .sync import sync_skb_folder, reindex_project
from .store import (
    get_project_dir,
    query_collection,
    query_multiple_collections,
    list_collections,
    list_documents_in_collection,
    delete_collection,
)
from .portability import export_source, import_source, export_index, import_index


async def _resolve_project_dir_from_ctx(ctx) -> str | None:
    """Resolve the client's working directory from MCP roots."""
    if ctx is None:
        return None
    try:
        roots_result = await ctx.session.list_roots()
        if roots_result.roots:
            return unquote(str(roots_result.roots[0].uri.path))
    except Exception:
        pass
    return None


async def tool_sync_skb(
    project_dir: str = "",
    progress_callback: Callable | None = None,
    log_callback: Callable | None = None,
    ctx=None,
) -> dict:
    """Scan the .skb/ folder in the project directory and ingest/update all files.

    Args:
        project_dir: Path to the project root. Defaults to current working directory.
        progress_callback: Optional async callable(current, total) for progress reporting.
        log_callback: Optional async callable(message) for log notifications.
        ctx: MCP context for resolving client working directory.
    """
    if not project_dir:
        resolved = await _resolve_project_dir_from_ctx(ctx)
        project_dir = resolved or str(Path.cwd())
    return await sync_skb_folder(project_dir, progress_callback=progress_callback, log_callback=log_callback)


async def tool_provision_skb(
    project_dir: str = "",
    force: bool = False,
    log_callback: Callable | None = None,
    ctx=None,
) -> dict:
    """Provision SKB into the current project.

    Args:
        project_dir: Path to the project root. Defaults to current working directory.
        force: If True, overwrite generated SKB files when they differ from the templates.
        log_callback: Optional async callable(message) for log notifications.
        ctx: MCP context for resolving client working directory.
    """
    if not project_dir:
        resolved = await _resolve_project_dir_from_ctx(ctx)
        project_dir = resolved or str(Path.cwd())
    return await provision_project(project_dir, force=force, log_callback=log_callback)


async def tool_search_docs(
    query: str,
    n_results: int = 5,
    project: str = "",
    search_all_projects: bool = False,
    ctx=None,
) -> dict:
    """Search the project knowledge base for relevant documentation.

    Args:
        query: Semantic search query.
        n_results: Number of results to return (default 5).
        project: Project name to search in. Defaults to current project.
        search_all_projects: If True, search across all indexed projects.
        ctx: MCP context for resolving client working directory.
    """
    if search_all_projects:
        results = query_multiple_collections(query, n_results)
    else:
        if not project:
            resolved = await _resolve_project_dir_from_ctx(ctx)
            project = Path(resolved).name if resolved else Path.cwd().name
        results = query_collection(project, query, n_results)

    return {
        "query": query,
        "results": results,
        "count": len(results),
        "scope": "all_projects" if search_all_projects else project,
    }


async def tool_search_code(
    query: str,
    language: str = "",
    n_results: int = 5,
    ctx=None,
) -> dict:
    """Search the knowledge base for code examples and reference implementations.

    Args:
        query: Semantic search query about code.
        language: Optional language filter (e.g., "python", "typescript").
        n_results: Number of results to return (default 5).
        ctx: MCP context for resolving client working directory.
    """
    resolved = await _resolve_project_dir_from_ctx(ctx)
    project = Path(resolved).name if resolved else Path.cwd().name
    where = {"doc_type": "code"}
    if language:
        where = {"$and": [{"doc_type": "code"}, {"language": language}]}

    results = query_collection(project, query, n_results, where=where)

    return {
        "query": query,
        "language": language or "any",
        "results": results,
        "count": len(results),
    }


def tool_list_projects() -> dict:
    """List all indexed projects with document and chunk counts."""
    collections = list_collections()
    return {
        "projects": collections,
        "total_projects": len(collections),
    }


async def tool_list_documents(project: str = "", ctx=None) -> dict:
    """List all indexed files for a project with metadata.

    Args:
        project: Project name. Defaults to current project.
        ctx: MCP context for resolving client working directory.
    """
    if not project:
        resolved = await _resolve_project_dir_from_ctx(ctx)
        project = Path(resolved).name if resolved else Path.cwd().name
    docs = list_documents_in_collection(project)
    return {
        "project": project,
        "documents": docs,
        "total_documents": len(docs),
    }


def tool_remove_project(project: str) -> dict:
    """Remove all indexed data for a project.

    Args:
        project: Name of the project to remove.
    """
    existed = delete_collection(project)
    return {
        "project": project,
        "removed": existed,
        "message": f"Project '{project}' removed." if existed else f"Project '{project}' not found.",
    }


async def tool_reindex_project(
    project: str = "",
    project_dir: str = "",
    progress_callback: Callable | None = None,
    log_callback: Callable | None = None,
    ctx=None,
) -> dict:
    """Force a full reindex: delete all indexed data and rebuild from scratch.

    Args:
        project: Project name. Used to look up the project directory if project_dir is empty.
        project_dir: Path to the project root. Defaults to current working directory.
        progress_callback: Optional async callable(current, total) for progress reporting.
        log_callback: Optional async callable(message) for log notifications.
        ctx: MCP context for resolving client working directory.
    """
    if not project_dir:
        if project:
            resolved = get_project_dir(project)
            if not resolved:
                return {"error": f"Could not resolve directory for project '{project}'. Index it first with sync_skb."}
            project_dir = resolved
        else:
            resolved = await _resolve_project_dir_from_ctx(ctx)
            project_dir = resolved or str(Path.cwd())

    return await reindex_project(project_dir, progress_callback=progress_callback, log_callback=log_callback)


async def tool_export_skb(
    project_dir: str = "",
    output_path: str = "",
    log_callback: Callable | None = None,
    ctx=None,
) -> dict:
    """Export .skb/ source files as a portable .tar.gz archive.

    Args:
        project_dir: Path to the project root. Defaults to current working directory.
        output_path: Where to write the archive. Defaults to <project_dir>/<project>-skb-source.tar.gz.
        log_callback: Optional async callable(message) for log notifications.
        ctx: MCP context for resolving client working directory.
    """
    if not project_dir:
        resolved = await _resolve_project_dir_from_ctx(ctx)
        project_dir = resolved or str(Path.cwd())
    return await export_source(project_dir, output_path=output_path, log_callback=log_callback)


async def tool_import_skb(
    archive_path: str,
    project_dir: str = "",
    merge: bool = True,
    run_sync: bool = True,
    log_callback: Callable | None = None,
    progress_callback: Callable | None = None,
    ctx=None,
) -> dict:
    """Import a source archive into a project's .skb/ folder.

    Args:
        archive_path: Path to the .tar.gz archive.
        project_dir: Target project root. Defaults to current working directory.
        merge: If True, merge with existing files. If False, wipe .skb/ first.
        run_sync: If True, run sync after extraction.
        log_callback: Optional async callable(message) for log notifications.
        progress_callback: Optional async callable(current, total) for progress.
        ctx: MCP context for resolving client working directory.
    """
    if not project_dir:
        resolved = await _resolve_project_dir_from_ctx(ctx)
        project_dir = resolved or str(Path.cwd())
    return await import_source(
        archive_path, project_dir=project_dir, merge=merge, run_sync=run_sync,
        log_callback=log_callback, progress_callback=progress_callback,
    )


async def tool_export_index(
    project: str = "",
    output_path: str = "",
    log_callback: Callable | None = None,
    ctx=None,
) -> dict:
    """Export vector index as gzipped JSONL.

    Args:
        project: Project name. Defaults to current project.
        output_path: Where to write the archive. Defaults to <cwd>/<project>-skb-index.jsonl.gz.
        log_callback: Optional async callable(message) for log notifications.
        ctx: MCP context for resolving client working directory.
    """
    if not project:
        resolved = await _resolve_project_dir_from_ctx(ctx)
        project = Path(resolved).name if resolved else Path.cwd().name
    return await export_index(project, output_path=output_path, log_callback=log_callback)


async def tool_import_index(
    archive_path: str,
    project: str = "",
    log_callback: Callable | None = None,
    progress_callback: Callable | None = None,
    ctx=None,
) -> dict:
    """Import a gzipped JSONL index archive into ChromaDB.

    Args:
        archive_path: Path to the .jsonl.gz archive.
        project: Target project name. If empty, uses project from archive header.
        log_callback: Optional async callable(message) for log notifications.
        progress_callback: Optional async callable(current, total) for progress.
        ctx: MCP context for resolving client working directory.
    """
    return await import_index(
        archive_path, project=project,
        log_callback=log_callback, progress_callback=progress_callback,
    )
