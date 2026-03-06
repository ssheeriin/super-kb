"""MCP tool definitions for the SKB server."""

from pathlib import Path

from .sync import sync_skb_folder
from .store import (
    query_collection,
    query_multiple_collections,
    list_collections,
    list_documents_in_collection,
    delete_collection,
)


def tool_sync_skb(project_dir: str = "") -> dict:
    """Scan the .skb/ folder in the project directory and ingest/update all files.

    Args:
        project_dir: Path to the project root. Defaults to current working directory.
    """
    if not project_dir:
        project_dir = str(Path.cwd())
    return sync_skb_folder(project_dir)


def tool_search_docs(
    query: str,
    n_results: int = 5,
    project: str = "",
    search_all_projects: bool = False,
) -> dict:
    """Search the project knowledge base for relevant documentation.

    Args:
        query: Semantic search query.
        n_results: Number of results to return (default 5).
        project: Project name to search in. Defaults to current project.
        search_all_projects: If True, search across all indexed projects.
    """
    if search_all_projects:
        results = query_multiple_collections(query, n_results)
    else:
        if not project:
            project = Path.cwd().name
        results = query_collection(project, query, n_results)

    return {
        "query": query,
        "results": results,
        "count": len(results),
        "scope": "all_projects" if search_all_projects else project,
    }


def tool_search_code(
    query: str,
    language: str = "",
    n_results: int = 5,
) -> dict:
    """Search the knowledge base for code examples and reference implementations.

    Args:
        query: Semantic search query about code.
        language: Optional language filter (e.g., "python", "typescript").
        n_results: Number of results to return (default 5).
    """
    project = Path.cwd().name
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


def tool_list_documents(project: str = "") -> dict:
    """List all indexed files for a project with metadata.

    Args:
        project: Project name. Defaults to current project.
    """
    if not project:
        project = Path.cwd().name
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
