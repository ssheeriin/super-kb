"""FlashRank cross-encoder reranker — retrieve-then-rerank pipeline.

Lazy-loads the model on first use. Degrades gracefully: if FlashRank is
unavailable (import error, download failure, disabled), rerank() returns
the input list truncated to top_n — identical to pre-reranker behavior.
"""

import logging
from typing import Any

from .config import RERANK_ENABLED, RERANK_MAX_LENGTH, RERANK_MODEL

logger = logging.getLogger(__name__)

# Three-state: None = not attempted, object = loaded, False = permanently failed
_ranker: Any = None
_attempted: bool = False


def _get_ranker() -> Any:
    """Lazy-load the FlashRank Ranker singleton."""
    global _ranker, _attempted
    if _attempted:
        return _ranker

    _attempted = True

    if not RERANK_ENABLED:
        logger.info("Reranker disabled via SKB_RERANK_ENABLED.")
        _ranker = None
        return _ranker

    try:
        from flashrank import Ranker

        _ranker = Ranker(model_name=RERANK_MODEL, max_length=RERANK_MAX_LENGTH)
        logger.info("FlashRank reranker loaded (model=%s).", RERANK_MODEL)
    except Exception:
        logger.warning("FlashRank reranker unavailable — falling back to embedding-only ranking.", exc_info=True)
        _ranker = None

    return _ranker


def rerank(query: str, results: list[dict], top_n: int) -> list[dict]:
    """Rerank results using FlashRank cross-encoder.

    Each result dict must have a "content" key. On success, each returned
    dict gets ``score`` replaced with the cross-encoder score, and the
    original cosine similarity preserved as ``embedding_score``.

    Falls back to ``results[:top_n]`` if the reranker is unavailable.
    """
    ranker = _get_ranker()
    if ranker is None or not results:
        return results[:top_n]

    try:
        from flashrank import RerankRequest

        # Stash the original dict in meta for zero-copy round-trip
        passages = [
            {"id": i, "text": r["content"], "meta": r}
            for i, r in enumerate(results)
        ]
        request = RerankRequest(query=query, passages=passages)
        ranked = ranker.rerank(request)

        out: list[dict] = []
        for item in ranked[:top_n]:
            original = item["meta"]
            original["embedding_score"] = original["score"]
            original["score"] = item["score"]
            out.append(original)
        return out

    except Exception:
        logger.warning("Reranking failed — returning embedding-ranked results.", exc_info=True)
        return results[:top_n]


def warm_up() -> None:
    """Pre-load the reranker model during server startup."""
    _get_ranker()
