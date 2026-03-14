"""Custom ONNX embedding function using BAAI/bge-small-en-v1.5.

This replaces ChromaDB's default all-MiniLM-L6-v2 (MTEB retrieval ~41)
with bge-small-en-v1.5 (MTEB retrieval ~51.68). Same 384 dimensions,
zero new pip dependencies — onnxruntime and tokenizers are already
transitive deps of chromadb.
"""

import importlib
import logging
import os
import shutil
import ssl
import urllib.request
from functools import cached_property
from pathlib import Path
from typing import Any, Dict, List, cast

import certifi
import numpy as np
import numpy.typing as npt

from chromadb.api.types import Documents, Embeddings, EmbeddingFunction, Space

from .config import EMBEDDING_MODEL_DIR

logger = logging.getLogger(__name__)

# HuggingFace repo and files needed for ONNX inference
_MODEL_REPO = "BAAI/bge-small-en-v1.5"
_HF_BASE_URL = f"https://huggingface.co/{_MODEL_REPO}/resolve/main"
_MODEL_FILES = ["onnx/model.onnx", "tokenizer.json"]
_MAX_TOKENS = 512
_QUERY_PREFIX = "Represent this sentence for searching relevant passages: "


class BGESmallEmbedding(EmbeddingFunction[Documents]):
    """bge-small-en-v1.5 via ONNX, with lazy download and caching."""

    def __init__(self) -> None:
        try:
            self.ort = importlib.import_module("onnxruntime")
        except ImportError:
            raise ValueError(
                "onnxruntime is required. Install with: pip install onnxruntime"
            )
        try:
            self.Tokenizer = importlib.import_module("tokenizers").Tokenizer
        except ImportError:
            raise ValueError(
                "tokenizers is required. Install with: pip install tokenizers"
            )

    # ── Download ────────────────────────────────────────────────────────

    def download_if_needed(self) -> None:
        """Download model files from HuggingFace if not already cached."""
        EMBEDDING_MODEL_DIR.mkdir(parents=True, exist_ok=True)
        for rel_path in _MODEL_FILES:
            local_path = EMBEDDING_MODEL_DIR / rel_path
            if local_path.exists():
                continue
            local_path.parent.mkdir(parents=True, exist_ok=True)
            url = f"{_HF_BASE_URL}/{rel_path}"
            logger.info("Downloading %s → %s", url, local_path)
            _download_to_path(url, local_path)
            logger.info("Downloaded %s", local_path.name)

    # ── Lazy-loaded resources ───────────────────────────────────────────

    @cached_property
    def tokenizer(self) -> Any:
        tok = self.Tokenizer.from_file(
            str(EMBEDDING_MODEL_DIR / "tokenizer.json")
        )
        tok.enable_truncation(max_length=_MAX_TOKENS)
        tok.enable_padding(pad_id=0, pad_token="[PAD]", length=_MAX_TOKENS)
        return tok

    @cached_property
    def model(self) -> Any:
        so = self.ort.SessionOptions()
        so.log_severity_level = 3
        so.graph_optimization_level = self.ort.GraphOptimizationLevel.ORT_ENABLE_ALL

        providers = self.ort.get_available_providers()
        if "CoreMLExecutionProvider" in providers:
            providers.remove("CoreMLExecutionProvider")

        return self.ort.InferenceSession(
            str(EMBEDDING_MODEL_DIR / "onnx" / "model.onnx"),
            providers=providers,
            sess_options=so,
        )

    # ── Forward pass ────────────────────────────────────────────────────

    def _forward(
        self, documents: List[str], batch_size: int = 32
    ) -> npt.NDArray[np.float32]:
        all_embeddings = []
        for i in range(0, len(documents), batch_size):
            batch = documents[i : i + batch_size]
            encoded = [self.tokenizer.encode(d) for d in batch]

            input_ids = np.array([e.ids for e in encoded], dtype=np.int64)
            attention_mask = np.array(
                [e.attention_mask for e in encoded], dtype=np.int64
            )
            token_type_ids = np.zeros_like(input_ids, dtype=np.int64)

            model_output = self.model.run(
                None,
                {
                    "input_ids": input_ids,
                    "attention_mask": attention_mask,
                    "token_type_ids": token_type_ids,
                },
            )
            last_hidden_state = model_output[0]

            # Mean pooling with attention mask weighting
            mask_expanded = np.broadcast_to(
                np.expand_dims(attention_mask, -1), last_hidden_state.shape
            )
            embeddings = np.sum(
                last_hidden_state * mask_expanded, axis=1
            ) / np.clip(mask_expanded.sum(axis=1), a_min=1e-9, a_max=None)

            # L2 normalize
            norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
            norms = np.clip(norms, a_min=1e-12, a_max=None)
            embeddings = (embeddings / norms).astype(np.float32)

            all_embeddings.append(embeddings)

        return np.concatenate(all_embeddings)

    # ── ChromaDB EmbeddingFunction protocol ─────────────────────────────

    def __call__(self, input: Documents) -> Embeddings:
        """Embed documents (no query prefix)."""
        self.download_if_needed()
        embeddings = self._forward(input)
        return cast(
            Embeddings,
            [np.array(e, dtype=np.float32) for e in embeddings],
        )

    def embed_query(self, input: Documents) -> Embeddings:
        """Embed queries with the BGE instruction prefix for better retrieval."""
        self.download_if_needed()
        prefixed = [f"{_QUERY_PREFIX}{doc}" for doc in input]
        embeddings = self._forward(prefixed)
        return cast(
            Embeddings,
            [np.array(e, dtype=np.float32) for e in embeddings],
        )

    @staticmethod
    def name() -> str:
        return "bge_small_en_v1_5"

    def default_space(self) -> Space:
        return "cosine"

    def supported_spaces(self) -> List[Space]:
        return ["cosine", "l2", "ip"]

    @staticmethod
    def build_from_config(config: Dict[str, Any]) -> "BGESmallEmbedding":
        return BGESmallEmbedding()

    def get_config(self) -> Dict[str, Any]:
        return {}


# ── Module-level singleton ──────────────────────────────────────────────

_embedding_fn: BGESmallEmbedding | None = None


def get_embedding_function() -> BGESmallEmbedding:
    global _embedding_fn
    if _embedding_fn is None:
        _embedding_fn = BGESmallEmbedding()
    return _embedding_fn


def _download_to_path(url: str, destination: Path) -> None:
    """Download a file with an explicit CA bundle for packaged binaries."""
    context = ssl.create_default_context(cafile=certifi.where())
    with urllib.request.urlopen(url, context=context) as response, destination.open("wb") as output:
        shutil.copyfileobj(response, output)
