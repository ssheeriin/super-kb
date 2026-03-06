"""SKB MCP Server — Shared Knowledge Base for Claude Code.

Entry point: run with `uv run server.py`
"""

from mcp.server.fastmcp import FastMCP

from skb.tools import (
    tool_sync_skb,
    tool_search_docs,
    tool_search_code,
    tool_list_projects,
    tool_list_documents,
    tool_remove_project,
)

mcp = FastMCP(
    "skb",
    instructions=(
        "Shared Knowledge Base (SKB) — a local vector knowledge base. "
        "Each project may have a .skb/ folder with context documents. "
        "Use sync_skb to index them, then search_docs/search_code to query."
    ),
)


@mcp.tool()
def sync_skb(project_dir: str = "") -> dict:
    """Scan the .skb/ folder in the project directory and ingest/update all files.

    Call this at the start of a session or after adding new files to .skb/.
    Input: project_dir (str, optional — defaults to current working directory).
    Output: {project, files_added, files_updated, files_removed, total_chunks}
    """
    return tool_sync_skb(project_dir)


@mcp.tool()
def search_docs(
    query: str,
    n_results: int = 5,
    project: str = "",
    search_all_projects: bool = False,
) -> dict:
    """Search the project knowledge base for relevant documentation, design decisions, API references, and code examples.

    Use this when the user asks about project architecture, conventions, or
    implementation details instead of asking them to provide files.
    Searches the .skb/ indexed documents semantically.

    Input:
      - query: what to search for
      - n_results: how many results (default 5)
      - project: which project (defaults to current)
      - search_all_projects: set True to search across all indexed projects
    """
    return tool_search_docs(query, n_results, project, search_all_projects)


@mcp.tool()
def search_code(
    query: str,
    language: str = "",
    n_results: int = 5,
) -> dict:
    """Search the knowledge base for code examples and reference implementations.

    Filters results to code file types only. Use when looking for code patterns,
    snippets, or implementation examples from .skb/.

    Input:
      - query: what code to search for
      - language: optional filter (e.g., "python", "typescript")
      - n_results: how many results (default 5)
    """
    return tool_search_code(query, language, n_results)


@mcp.tool()
def list_projects() -> dict:
    """List all indexed projects with document and chunk counts.

    Shows every project that has been synced into the knowledge base.
    """
    return tool_list_projects()


@mcp.tool()
def list_documents(project: str = "") -> dict:
    """List all indexed files for a project with metadata.

    Shows source paths, chunk counts, and last synced timestamps for all
    documents in a project's knowledge base.

    Input: project (str, optional — defaults to current project)
    """
    return tool_list_documents(project)


@mcp.tool()
def remove_project(project: str) -> dict:
    """Remove all indexed data for a project.

    Use when a project is archived or you want to clear its knowledge base.

    Input: project (str) — name of the project to remove
    """
    return tool_remove_project(project)


if __name__ == "__main__":
    mcp.run()
