"""Product chatbot endpoint with semantic similarity gate.

Decision flow:
  1. Reject obvious prompt-injection / oversize input → HTTP 400.
  2. Compute semantic similarity of the question to every KB chunk via the
     HuggingFace Inference API (sentence-transformers/all-MiniLM-L6-v2,
     normalized, cosine).
  3. If max_similarity < LOW_THRESHOLD → hard refusal, no LLM call.
  4. Otherwise call the LLM with the top-K matching chunks injected into
     the system prompt. The LLM-side scope guardrail (Layer 3) is
     disabled — the model just answers in plain Markdown. The semantic
     gate above is the only off-topic filter at the LLM stage.
  5. Always return `similarity` and `decision_path` so the operator can
     tune the threshold against real questions.

Thresholds are configurable via PREPULSE_KB_LOW_THRESHOLD and
PREPULSE_KB_HIGH_THRESHOLD.
"""

from __future__ import annotations

import os
from typing import Literal

from fastapi import APIRouter, HTTPException
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from backend.llm import get_llm
from backend.prompts.chatbot import REFUSAL, build_system_prompt
from backend.safety import check_chat_input
from backend.services.kb_embeddings import index_size, score_query
from backend.services.knowledge import corpus_chars, doc_count, load_corpus

router = APIRouter()


def _threshold(name: str, default: float) -> float:
    raw = os.getenv(name)
    if not raw:
        return default
    try:
        return float(raw)
    except ValueError:
        return default


# Calibrated against sentence-transformers/all-MiniLM-L6-v2 + the seeded KB:
#   off-topic floor (sourdough / weather / world-cup) tops out around 0.17
#   in-scope floor (MITRE / ROI / Remediator paraphrases) bottoms out around 0.37
# 0.35 catches the off-topic band more aggressively while staying under the
# in-scope floor; F-27 (validation campaign) showed 7/30 off-topic answers
# slipping past 0.25, so we raise the gate.
LOW_THRESHOLD = _threshold("PREPULSE_KB_LOW_THRESHOLD", 0.35)
HIGH_THRESHOLD = _threshold("PREPULSE_KB_HIGH_THRESHOLD", 0.65)


class ChatTurn(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(..., max_length=4000)


class ChatRequest(BaseModel):
    messages: list[ChatTurn] = Field(..., min_length=1, max_length=20)


class TopChunk(BaseModel):
    filename: str
    similarity: float
    preview: str


class ChatResponse(BaseModel):
    answer: str
    is_in_scope: bool
    similarity: float
    decision_path: Literal["similarity_low", "llm_in_scope", "llm_refused", "parse_failed"]
    top_chunks: list[TopChunk] = []
    refusal_sentence: str = REFUSAL
    # Which provider + model actually answered. Populated from the LLM
    # response metadata. Empty string when no LLM call was made (e.g.
    # similarity_low) or when the metadata didn't carry a model name.
    provider: str = ""
    model: str = ""


def _classify_provider(model_name: str) -> str:
    """Map a model name string to its provider label."""
    if not model_name:
        return ""
    n = model_name.lower()
    if n.startswith("claude"):
        return "anthropic"
    if n.startswith("deepseek"):
        return "deepseek"
    if n.startswith(("gpt", "o1", "o3", "o4")):
        return "openai"
    return "unknown"


def _extract_model(resp) -> str:
    """Pull the model name out of an AIMessage / langchain response."""
    meta = getattr(resp, "response_metadata", None) or {}
    # ChatAnthropic uses "model"; ChatOpenAI uses "model_name"
    return str(meta.get("model") or meta.get("model_name") or "")


def _format_retrieved_chunks(top_chunks: list[dict]) -> str:
    if not top_chunks:
        return "(no chunks retrieved)"
    lines: list[str] = []
    for i, c in enumerate(top_chunks, 1):
        lines.append(
            f"## Chunk {i} · similarity={c['similarity']:.2f} · {c['filename']}\n{c['text']}"
        )
    return "\n\n".join(lines)


def _public_chunks(top_chunks: list[dict]) -> list[TopChunk]:
    out: list[TopChunk] = []
    for c in top_chunks:
        out.append(
            TopChunk(
                filename=c["filename"],
                similarity=c["similarity"],
                preview=c["text"][:200] + ("…" if len(c["text"]) > 200 else ""),
            )
        )
    return out


@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest) -> ChatResponse:
    last = req.messages[-1]
    if last.role != "user":
        raise HTTPException(400, {"error": "last_message_must_be_user"})
    check_chat_input(last.content)

    embedding_available = True
    try:
        sim = await score_query(last.content, top_k=3)
    except RuntimeError:
        # Embedding service unavailable (no HF token, network down, etc.).
        # Fail OPEN: skip the similarity gate, let the LLM-only guardrail decide.
        embedding_available = False
        sim = {"max_similarity": 0.0, "top_chunks": []}
    similarity = float(sim["max_similarity"])
    top_chunks = sim["top_chunks"]
    public = _public_chunks(top_chunks)

    # Layer 1: hard refuse if the question is clearly off-topic.
    # Only enforce when the embedding service actually answered.
    if embedding_available and similarity < LOW_THRESHOLD:
        return ChatResponse(
            answer=REFUSAL,
            is_in_scope=False,
            similarity=similarity,
            decision_path="similarity_low",
            top_chunks=public,
        )

    # Layer 2: LLM call. Pass retrieved chunks so the model has the right
    # context immediately; the looser prompt leans toward answering.
    corpus = load_corpus()
    retrieved = _format_retrieved_chunks(top_chunks)
    system = SystemMessage(content=build_system_prompt(corpus, retrieved=retrieved))

    history: list = [system]
    for turn in req.messages:
        if turn.role == "user":
            history.append(HumanMessage(content=turn.content))
        else:
            history.append(AIMessage(content=turn.content))

    llm = get_llm("primary")
    try:
        resp = await llm.ainvoke(history)
    except Exception as e:
        raise HTTPException(502, {"error": "llm_call_failed", "reason": str(e)[:200]})

    text = resp.content if isinstance(resp.content, str) else ""
    if not isinstance(resp.content, str):
        for block in resp.content:
            if isinstance(block, dict) and block.get("type") == "text":
                text += block.get("text", "")
            elif isinstance(block, str):
                text += block

    model_name = _extract_model(resp)
    provider = _classify_provider(model_name)

    # Layer 3 (LLM-side scope guardrail) disabled — take the model's text
    # verbatim. The semantic similarity gate above is the only off-topic
    # filter at the LLM stage; jailbreak attempts are still caught upstream
    # by the prompt-injection regex in safety.check_chat_input().
    answer = text.strip()
    if not answer:
        # extremely rare: empty model response. Return the refusal so the
        # frontend has something to render.
        return ChatResponse(
            answer=REFUSAL,
            is_in_scope=False,
            similarity=similarity,
            decision_path="llm_refused",
            top_chunks=public,
            provider=provider,
            model=model_name,
        )

    return ChatResponse(
        answer=answer,
        is_in_scope=True,
        similarity=similarity,
        decision_path="llm_in_scope",
        top_chunks=public,
        provider=provider,
        model=model_name,
    )


@router.get("/chat/health")
async def chat_health() -> dict:
    from backend.llm import available_providers

    return {
        "ok": True,
        "kb_doc_count": doc_count(),
        "kb_corpus_chars": corpus_chars(),
        "kb_chunk_count": index_size(),
        "low_threshold": LOW_THRESHOLD,
        "high_threshold": HIGH_THRESHOLD,
        "llm_providers": available_providers(),
    }
