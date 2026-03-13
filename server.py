"""SKB MCP Server — Super Knowledge Base for Claude Code.

Entry point: run with `uv run server.py`
"""

import logging
from contextlib import asynccontextmanager

from mcp.server.fastmcp import Context, FastMCP

from skb import store, reranker
from skb.tools import (
    tool_provision_skb,
    tool_sync_skb,
    tool_search_docs,
    tool_search_code,
    tool_list_projects,
    tool_list_documents,
    tool_remove_project,
    tool_reindex_project,
    tool_export_skb,
    tool_import_skb,
    tool_export_index,
    tool_import_index,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")


@asynccontextmanager
async def lifespan(server: FastMCP):
    """Warm up the ChromaDB embedding model at server startup."""
    store.warm_up()
    reranker.warm_up()
    yield


mcp = FastMCP(
    "skb",
    instructions=(
        "Super Knowledge Base (SKB) — a local vector knowledge base. "
        "Each project may have a .skb/ folder with context documents. "
        "Use provision_skb to bootstrap a project, sync_skb to index it, "
        "then search_docs/search_code to query."
    ),
    lifespan=lifespan,
)


@mcp.tool()
async def provision_skb(
    project_dir: str = "",
    force: bool = False,
    ctx: Context | None = None,
) -> dict:
    """Provision SKB into the current project.

    Creates a local `.skb/` folder, installs the project-local `skb` skill,
    writes `.claude/CLAUDE-skb.md`, and wires `CLAUDE.md` to import it.

    Input:
      - project_dir (str, optional): path to the project root — defaults to the current working directory
      - force (bool, optional): if True, overwrite generated SKB files when they differ from the templates
    """
    log_callback = (lambda msg: ctx.info(msg)) if ctx else None
    return await tool_provision_skb(project_dir, force=force, log_callback=log_callback, ctx=ctx)


@mcp.tool()
async def sync_skb(project_dir: str = "", ctx: Context | None = None) -> dict:
    """Scan the .skb/ folder in the project directory and ingest/update all files.

    Call this at the start of a session or after adding new files to .skb/.
    Input: project_dir (str, optional — defaults to current working directory).
    Output: {project, files_added, files_updated, files_removed, total_chunks}
    """
    progress_callback = ctx.report_progress if ctx else None
    log_callback = (lambda msg: ctx.info(msg)) if ctx else None
    return await tool_sync_skb(project_dir, progress_callback=progress_callback, log_callback=log_callback, ctx=ctx)


@mcp.tool()
async def search_docs(
    query: str,
    n_results: int = 5,
    project: str = "",
    search_all_projects: bool = False,
    ctx: Context | None = None,
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
    return await tool_search_docs(query, n_results, project, search_all_projects, ctx=ctx)


@mcp.tool()
async def search_code(
    query: str,
    language: str = "",
    n_results: int = 5,
    ctx: Context | None = None,
) -> dict:
    """Search the knowledge base for code examples and reference implementations.

    Filters results to code file types only. Use when looking for code patterns,
    snippets, or implementation examples from .skb/.

    Input:
      - query: what code to search for
      - language: optional filter (e.g., "python", "typescript")
      - n_results: how many results (default 5)
    """
    return await tool_search_code(query, language, n_results, ctx=ctx)


@mcp.tool()
def list_projects() -> dict:
    """List all indexed projects with document and chunk counts.

    Shows every project that has been synced into the knowledge base.
    """
    return tool_list_projects()


@mcp.tool()
async def list_documents(project: str = "", ctx: Context | None = None) -> dict:
    """List all indexed files for a project with metadata.

    Shows source paths, chunk counts, and last synced timestamps for all
    documents in a project's knowledge base.

    Input: project (str, optional — defaults to current project)
    """
    return await tool_list_documents(project, ctx=ctx)


@mcp.tool()
def remove_project(project: str) -> dict:
    """Remove all indexed data for a project.

    Use when a project is archived or you want to clear its knowledge base.

    Input: project (str) — name of the project to remove
    """
    return tool_remove_project(project)


@mcp.tool()
async def reindex_project(
    project: str = "",
    project_dir: str = "",
    ctx: Context | None = None,
) -> dict:
    """Force a full reindex: delete all indexed data for a project and rebuild from scratch.

    Use when the index is corrupted, embeddings need regenerating, or you want
    a clean slate without manually removing and re-syncing.

    Input:
      - project (str, optional): project name — used to look up the directory from stored metadata
      - project_dir (str, optional): explicit path to project root — takes precedence over project name
      - If both are empty, defaults to the current working directory
    """
    progress_callback = ctx.report_progress if ctx else None
    log_callback = (lambda msg: ctx.info(msg)) if ctx else None
    return await tool_reindex_project(project, project_dir, progress_callback=progress_callback, log_callback=log_callback, ctx=ctx)


@mcp.tool()
async def export_skb(
    project_dir: str = "",
    output_path: str = "",
    ctx: Context | None = None,
) -> dict:
    """Export .skb/ source files as a portable .tar.gz archive.

    Creates a tar.gz containing all files from the project's .skb/ folder
    plus a manifest.json. The recipient can import this archive to recreate
    the .skb/ folder and rebuild the index.

    Input:
      - project_dir (str, optional): path to project root — defaults to current working directory
      - output_path (str, optional): where to write the archive — defaults to <project_dir>/<project>-skb-source.tar.gz
    """
    log_callback = (lambda msg: ctx.info(msg)) if ctx else None
    return await tool_export_skb(project_dir, output_path, log_callback=log_callback, ctx=ctx)


@mcp.tool()
async def import_skb(
    archive_path: str,
    project_dir: str = "",
    merge: bool = True,
    run_sync: bool = True,
    ctx: Context | None = None,
) -> dict:
    """Import a source archive into a project's .skb/ folder.

    Extracts a .tar.gz source archive (created by export_skb) into the
    target project's .skb/ folder and optionally rebuilds the index.

    Input:
      - archive_path (str): path to the .tar.gz archive
      - project_dir (str, optional): target project root — defaults to current working directory
      - merge (bool, optional): if True (default), merge with existing files; if False, replace .skb/ entirely
      - run_sync (bool, optional): if True (default), rebuild the index after import
    """
    log_callback = (lambda msg: ctx.info(msg)) if ctx else None
    progress_callback = ctx.report_progress if ctx else None
    return await tool_import_skb(
        archive_path, project_dir, merge=merge, run_sync=run_sync,
        log_callback=log_callback, progress_callback=progress_callback, ctx=ctx,
    )


@mcp.tool()
async def export_index(
    project: str = "",
    output_path: str = "",
    ctx: Context | None = None,
) -> dict:
    """Export vector index as gzipped JSONL (.jsonl.gz).

    Exports all ChromaDB chunks and embeddings for a project as a compressed
    JSONL file. Fast to import (no re-embedding needed), but requires the
    same embedding model.

    Input:
      - project (str, optional): project name — defaults to current project
      - output_path (str, optional): where to write the archive — defaults to <cwd>/<project>-skb-index.jsonl.gz
    """
    log_callback = (lambda msg: ctx.info(msg)) if ctx else None
    return await tool_export_index(project, output_path, log_callback=log_callback, ctx=ctx)


@mcp.tool()
async def import_index(
    archive_path: str,
    project: str = "",
    ctx: Context | None = None,
) -> dict:
    """Import a gzipped JSONL index archive into ChromaDB.

    Imports pre-computed embeddings from a .jsonl.gz archive (created by
    export_index) directly into ChromaDB, bypassing the embedding step.

    Input:
      - archive_path (str): path to the .jsonl.gz archive
      - project (str, optional): target project name — if empty, uses the project name from the archive header
    """
    log_callback = (lambda msg: ctx.info(msg)) if ctx else None
    progress_callback = ctx.report_progress if ctx else None
    return await tool_import_index(
        archive_path, project=project,
        log_callback=log_callback, progress_callback=progress_callback, ctx=ctx,
    )


if __name__ == "__main__":
    mcp.run()
