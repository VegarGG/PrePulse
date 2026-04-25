"""Knowledge-base loader for the product chatbot.

Loads every `*.md` file under `backend/knowledge_base/` (except `README.md`)
at first call and caches the concatenation. The chatbot system prompt
embeds the full corpus, so the file budget is governed by the model's
context window — keep total content under ~30 KB to leave room for chat
history.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

KB_ROOT = Path(__file__).resolve().parents[1] / "knowledge_base"


@lru_cache(maxsize=1)
def load_corpus() -> str:
    if not KB_ROOT.exists():
        return ""
    files = sorted(p for p in KB_ROOT.glob("*.md") if p.name.lower() != "readme.md")
    chunks: list[str] = []
    for p in files:
        chunks.append(f"<doc filename=\"{p.name}\">\n{p.read_text()}\n</doc>")
    return "\n\n".join(chunks)


def doc_count() -> int:
    if not KB_ROOT.exists():
        return 0
    return sum(1 for p in KB_ROOT.glob("*.md") if p.name.lower() != "readme.md")


def corpus_chars() -> int:
    return len(load_corpus())


def reload_corpus() -> None:
    """Clear the cache so the next call re-reads the disk. Used by tests."""
    load_corpus.cache_clear()
