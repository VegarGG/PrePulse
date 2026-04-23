"""Lazy MITRE ATT&CK vector store.

Loaded from backend/data/attack_enterprise.json on first call. Uses deterministic
fake embeddings by default so the demo works offline; swap in OpenAIEmbeddings
when running live with a real API key.
"""

from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path
from typing import Any

_DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "attack_enterprise.json"


def _load_techniques() -> list[dict[str, Any]]:
    if not _DATA_PATH.exists():
        return []
    raw = json.loads(_DATA_PATH.read_text())
    techniques: list[dict[str, Any]] = []
    for obj in raw.get("objects", []):
        if obj.get("type") != "attack-pattern":
            continue
        if obj.get("revoked") or obj.get("x_mitre_deprecated"):
            continue
        ext_refs = obj.get("external_references", [])
        mitre_ref = next(
            (r for r in ext_refs if r.get("source_name") == "mitre-attack"),
            None,
        )
        if not mitre_ref:
            continue
        phases = obj.get("kill_chain_phases", [])
        tactic = phases[0].get("phase_name", "").replace("-", " ").title() if phases else ""
        techniques.append(
            {
                "technique_id": mitre_ref.get("external_id", ""),
                "name": obj.get("name", ""),
                "tactic": tactic,
                "description": (obj.get("description") or "")[:600],
            }
        )
    return techniques


@lru_cache(maxsize=1)
def get_retriever():
    """Return a retriever. Embedding choice:
    - if OPENAI_API_KEY set → OpenAIEmbeddings
    - else → DeterministicFakeEmbedding (offline-safe fallback).
    """
    from langchain_core.documents import Document
    from langchain_core.vectorstores import InMemoryVectorStore

    techniques = _load_techniques()
    docs = [
        Document(
            page_content=f"{t['name']}. {t['description']}",
            metadata={
                "technique_id": t["technique_id"],
                "name": t["name"],
                "tactic": t["tactic"],
            },
        )
        for t in techniques
    ]

    if os.getenv("OPENAI_API_KEY") and os.getenv("PREPULSE_LIVE") == "1":
        from langchain_openai import OpenAIEmbeddings

        embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    else:
        from langchain_core.embeddings import DeterministicFakeEmbedding

        embeddings = DeterministicFakeEmbedding(size=256)

    store = InMemoryVectorStore.from_documents(docs, embeddings)
    return store.as_retriever(search_kwargs={"k": 5})


def technique_count() -> int:
    return len(_load_techniques())
