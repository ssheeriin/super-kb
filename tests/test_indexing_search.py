import asyncio
import os
from pathlib import Path

import pytest
from chromadb.api.types import Documents, EmbeddingFunction, Embeddings

from skb import store
from skb.tools import tool_list_documents, tool_list_projects, tool_search_code, tool_search_docs, tool_sync_skb


class KeywordEmbedding(EmbeddingFunction[Documents]):
    """Deterministic embedding function for Chroma integration tests."""

    KEYWORDS = (
        ("architecture", "tenant", "onboarding", "design"),
        ("retry", "backoff", "python", "decorator"),
        ("build", "install", "release", "package"),
    )

    def __init__(self) -> None:
        pass

    def __call__(self, input: Documents) -> Embeddings:
        vectors: list[list[float]] = []
        for text in input:
            lower = text.lower()
            counts = [float(sum(lower.count(term) for term in group)) for group in self.KEYWORDS]
            counts.append(float(len(lower.split()) or 1))
            vectors.append(counts)
        return vectors

    @staticmethod
    def name() -> str:
        return "keyword-test"

    @staticmethod
    def build_from_config(_config: dict) -> "KeywordEmbedding":
        return KeywordEmbedding()

    def get_config(self) -> dict:
        return {}


@pytest.fixture()
def isolated_vector_store(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    chromadb_dir = tmp_path / "chromadb"
    monkeypatch.setattr(store, "CHROMADB_DIR", chromadb_dir)
    monkeypatch.setattr(store, "_client", None)
    monkeypatch.setattr(store, "get_embedding_function", lambda: KeywordEmbedding())
    monkeypatch.setattr(store, "rerank_results", lambda _query, results, top_n: results[:top_n])
    yield chromadb_dir
    store._client = None


def test_sync_and_search_round_trip(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, isolated_vector_store: Path) -> None:
    project_dir = tmp_path / "demo-project"
    docs_dir = project_dir / ".skb"
    project_dir.mkdir()

    _write_file(
        docs_dir / "architecture.md",
        """# Tenant Onboarding Architecture

This document explains the tenant onboarding architecture and service design.
Use this as the main architecture reference for onboarding flows.
""",
    )
    _write_file(
        docs_dir / "examples" / "retry.py",
        '''"""Python retry decorator example."""

def retry_with_backoff(operation):
    for attempt in range(3):
        try:
            return operation()
        except RuntimeError:
            continue
    raise RuntimeError("retry failed")
''',
    )

    sync_result = asyncio.run(tool_sync_skb(project_dir=str(project_dir)))

    assert sync_result["files_added"] == 2
    assert sync_result["files_updated"] == 0
    assert sync_result["files_removed"] == 0
    assert sync_result["total_chunks"] >= 2

    projects = tool_list_projects()
    assert projects["total_projects"] == 1
    assert projects["projects"][0]["project"] == "demo-project"

    documents = asyncio.run(tool_list_documents(project="demo-project"))
    assert documents["total_documents"] == 2
    assert {doc["source"] for doc in documents["documents"]} == {
        ".skb/architecture.md",
        ".skb/examples/retry.py",
    }

    docs_search = asyncio.run(tool_search_docs("tenant onboarding architecture", project="demo-project"))
    assert docs_search["count"] >= 1
    assert docs_search["results"][0]["source_file"] == ".skb/architecture.md"
    assert docs_search["results"][0]["doc_type"] == "markdown"

    monkeypatch.chdir(project_dir)
    code_search = asyncio.run(tool_search_code("python retry backoff", language="python"))
    assert code_search["count"] >= 1
    assert code_search["results"][0]["source_file"] == ".skb/examples/retry.py"
    assert code_search["results"][0]["language"] == "python"


def test_sync_detects_updates_and_deletions(tmp_path: Path, isolated_vector_store: Path) -> None:
    project_dir = tmp_path / "update-project"
    docs_dir = project_dir / ".skb"
    project_dir.mkdir()

    architecture = docs_dir / "architecture.md"
    retry_code = docs_dir / "examples" / "retry.py"
    _write_file(architecture, "# Initial Architecture\n\nTenant onboarding architecture notes.\n")
    _write_file(retry_code, "def retry_operation():\n    return 'ok'\n")

    first_sync = asyncio.run(tool_sync_skb(project_dir=str(project_dir)))
    assert first_sync["files_added"] == 2

    original_mtime = architecture.stat().st_mtime
    _write_file(
        architecture,
        "# Updated Architecture\n\nRelease build and install flow for tenant onboarding.\n",
    )
    updated_mtime = original_mtime + 5
    os.utime(architecture, (updated_mtime, updated_mtime))
    retry_code.unlink()
    _write_file(docs_dir / "release.md", "# Release Notes\n\nBuild install package release checklist.\n")

    second_sync = asyncio.run(tool_sync_skb(project_dir=str(project_dir)))

    assert second_sync["files_added"] == 1
    assert second_sync["files_updated"] == 1
    assert second_sync["files_removed"] == 1

    documents = asyncio.run(tool_list_documents(project="update-project"))
    assert {doc["source"] for doc in documents["documents"]} == {
        ".skb/architecture.md",
        ".skb/release.md",
    }

    search = asyncio.run(tool_search_docs("release build install", project="update-project"))
    assert search["count"] >= 1
    assert search["results"][0]["source_file"] == ".skb/release.md"


def _write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
