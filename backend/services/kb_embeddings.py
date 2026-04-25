"""Semantic-similarity gate for the chatbot — HuggingFace Inference API backend.

Uses HuggingFace's hosted feature-extraction endpoint with the
`sentence-transformers/all-MiniLM-L6-v2` model by default (384-dim,
free tier, fast). The KB markdown files are split into paragraph-level
chunks, embedded once on first call, and cached in-memory for the
process lifetime. Each user query is embedded and scored against every
chunk via cosine similarity (embeddings are L2-normalized, so dot
product = cosine).

Environment variables:
  HUGGINGFACE_API_TOKEN  (or HF_TOKEN)  — required, free tier OK
  PREPULSE_HF_EMBEDDING_MODEL           — override the default model

The chat endpoint reads `score_query(text)` and decides:
  - max_sim < LOW   → hard refuse, no LLM call
  - max_sim ≥ HIGH  → high-confidence answer (advisory; not enforced today)
  - in between      → LLM decides as before, retrieval still injected
"""

from __future__ import annotations

import asyncio
import os
import re
from typing import Any

import httpx
import numpy as np

from backend.services.knowledge import KB_ROOT

DEFAULT_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
HF_MODEL = os.getenv("PREPULSE_HF_EMBEDDING_MODEL", DEFAULT_MODEL)
# HF migrated their hosted inference to the router in late 2024. The classic
# api-inference.huggingface.co/pipeline/feature-extraction/<model> endpoint
# now returns 404. The replacement lives under the router and requires a
# token with the "Inference Providers" / "serverless Inference API" scope.
HF_API_URL = (
    f"https://router.huggingface.co/hf-inference/models/{HF_MODEL}"
    "/pipeline/feature-extraction"
)
_MIN_CHUNK_CHARS = 30
_HTTP_TIMEOUT_S = 60.0
_MAX_RETRIES = 4

# In-memory cache for the indexed corpus. Populated on first score_query() call.
_chunks_cache: list[tuple[str, str]] | None = None
_matrix_cache: np.ndarray | None = None
_index_lock = asyncio.Lock()


def _hf_token() -> str:
    tok = os.getenv("HUGGINGFACE_API_TOKEN") or os.getenv("HF_TOKEN")
    if not tok:
        raise RuntimeError(
            "HUGGINGFACE_API_TOKEN (or HF_TOKEN) not set. The chatbot's "
            "similarity gate calls the HuggingFace Inference API and needs "
            "a free token from https://huggingface.co/settings/tokens."
        )
    return tok


async def _embed_batch(texts: list[str]) -> np.ndarray:
    """Call the HF Inference API to embed a batch of texts.

    Handles the 503 "model is loading" case by waiting and retrying. Returns
    L2-normalized embeddings as a (N, dim) float32 numpy array.
    """
    if not texts:
        return np.zeros((0, 384), dtype=np.float32)

    headers = {"Authorization": f"Bearer {_hf_token()}"}
    body = {"inputs": texts, "options": {"wait_for_model": True}}

    last_error: str | None = None
    async with httpx.AsyncClient(timeout=_HTTP_TIMEOUT_S) as client:
        for attempt in range(_MAX_RETRIES):
            try:
                r = await client.post(HF_API_URL, json=body, headers=headers)
            except httpx.RequestError as e:
                last_error = f"network: {e}"
                await asyncio.sleep(2 ** attempt)
                continue

            if r.status_code == 200:
                data = r.json()
                arr = np.asarray(data, dtype=np.float32)
                # Some HF responses wrap a single input as 1-D — normalize shape
                if arr.ndim == 1:
                    arr = arr.reshape(1, -1)
                # The pipeline endpoint sometimes returns (N, seq_len, dim);
                # mean-pool along seq_len if so.
                if arr.ndim == 3:
                    arr = arr.mean(axis=1)
                norms = np.linalg.norm(arr, axis=1, keepdims=True)
                return arr / np.clip(norms, 1e-12, None)

            if r.status_code == 503:
                # Model is loading; HF returns estimated_time
                try:
                    payload = r.json()
                    wait = float(payload.get("estimated_time", 8.0))
                except Exception:
                    wait = 8.0
                await asyncio.sleep(min(wait, 30.0))
                last_error = f"503 (model loading, waited {wait:.0f}s)"
                continue

            # 401, 429, 5xx — capture and retry
            last_error = f"{r.status_code}: {r.text[:200]}"
            if r.status_code in (401, 403):
                # bad token — fail fast, retry won't help
                break
            await asyncio.sleep(2 ** attempt)

    raise RuntimeError(f"HF Inference API failed after retries: {last_error}")


def _chunk_corpus() -> list[tuple[str, str]]:
    if not KB_ROOT.exists():
        return []
    chunks: list[tuple[str, str]] = []
    for path in sorted(KB_ROOT.glob("*.md")):
        if path.name.lower() == "readme.md":
            continue
        text = path.read_text()
        for raw in re.split(r"\n\s*\n", text):
            para = raw.strip()
            if len(para) < _MIN_CHUNK_CHARS:
                continue
            chunks.append((path.name, para))
    return chunks


async def _ensure_index() -> tuple[list[tuple[str, str]], np.ndarray]:
    global _chunks_cache, _matrix_cache
    if _matrix_cache is not None and _chunks_cache is not None:
        return _chunks_cache, _matrix_cache

    async with _index_lock:
        if _matrix_cache is not None and _chunks_cache is not None:
            return _chunks_cache, _matrix_cache

        chunks = _chunk_corpus()
        if not chunks:
            _chunks_cache = []
            _matrix_cache = np.zeros((0, 384), dtype=np.float32)
            return _chunks_cache, _matrix_cache

        texts = [c[1] for c in chunks]
        matrix = await _embed_batch(texts)
        _chunks_cache = chunks
        _matrix_cache = matrix
    return _chunks_cache, _matrix_cache


def reload_index() -> None:
    """Drop the in-memory index. Next score_query() call will re-embed."""
    global _chunks_cache, _matrix_cache
    _chunks_cache = None
    _matrix_cache = None


def index_size() -> int:
    """Return the number of cached chunks. Zero if not yet built."""
    return 0 if _chunks_cache is None else len(_chunks_cache)


async def score_query(query: str, top_k: int = 3) -> dict[str, Any]:
    """Embed `query`, return cosine similarity to each chunk, surface top-k matches.

    Returns:
        {
          "max_similarity": float,
          "top_chunks": [{"filename": str, "text": str, "similarity": float}, ...]
        }
    """
    chunks, matrix = await _ensure_index()
    if matrix.shape[0] == 0 or not query.strip():
        return {"max_similarity": 0.0, "top_chunks": []}

    q_matrix = await _embed_batch([query])
    if q_matrix.shape[0] == 0:
        return {"max_similarity": 0.0, "top_chunks": []}
    q = q_matrix[0]

    sims = matrix @ q
    k = min(top_k, sims.shape[0])
    top_idx = np.argsort(sims)[::-1][:k]

    return {
        "max_similarity": float(sims[top_idx[0]]),
        "top_chunks": [
            {
                "filename": chunks[i][0],
                "text": chunks[i][1],
                "similarity": float(sims[i]),
            }
            for i in top_idx
        ],
    }
