"""LLM gateway with selectable provider + auto-fallback chain.

Three providers are supported:

    index  name        env key                  model env override        SDK path
    -----  ----------  -----------------------  -------------------------  --------
    0      anthropic   ANTHROPIC_API_KEY        ANTHROPIC_MODEL            langchain-anthropic
    1      openai      OPENAI_API_KEY           OPENAI_MODEL               langchain-openai
    2      deepseek    DEEPSEEK_API_KEY         DEEPSEEK_MODEL             langchain-openai (OpenAI-compatible)

The operator picks the *preferred* provider via `PREPULSE_API_PROVIDER`
(default 0 = Anthropic). The runtime then builds a chain that puts the
preferred provider first and the rest after as automatic fallbacks via
LangChain's `with_fallbacks`. Providers whose keys are not set are
skipped entirely. If only one provider is configured, the chain is
trivially that one provider with no fallbacks.

Temperature is fixed at 0.2 across providers for reproducibility (§14.4
of the architecture spec).
"""

from __future__ import annotations

import os
from typing import Callable

from langchain_core.language_models.chat_models import BaseChatModel

PROVIDER_INDEX: list[str] = ["anthropic", "openai", "deepseek"]

DEFAULT_MODELS: dict[str, str] = {
    "anthropic": "claude-sonnet-4-6",
    "openai": "gpt-4o",
    "deepseek": "deepseek-v4-flash",
}

DEEPSEEK_BASE_URL = "https://api.deepseek.com/v1"


def _build_anthropic() -> BaseChatModel | None:
    if not os.getenv("ANTHROPIC_API_KEY"):
        return None
    from langchain_anthropic import ChatAnthropic

    return ChatAnthropic(
        model=os.getenv("ANTHROPIC_MODEL", DEFAULT_MODELS["anthropic"]),
        temperature=0.2,
        max_tokens=2048,
        timeout=90,
        max_retries=2,
    )


def _build_openai() -> BaseChatModel | None:
    if not os.getenv("OPENAI_API_KEY"):
        return None
    from langchain_openai import ChatOpenAI

    return ChatOpenAI(
        model=os.getenv("OPENAI_MODEL", DEFAULT_MODELS["openai"]),
        temperature=0.2,
        max_tokens=2048,
        timeout=90,
        max_retries=2,
    )


def _build_deepseek() -> BaseChatModel | None:
    if not os.getenv("DEEPSEEK_API_KEY"):
        return None
    from langchain_openai import ChatOpenAI

    # DeepSeek is OpenAI-compatible; we reuse ChatOpenAI with their base URL.
    return ChatOpenAI(
        model=os.getenv("DEEPSEEK_MODEL", DEFAULT_MODELS["deepseek"]),
        api_key=os.environ["DEEPSEEK_API_KEY"],
        base_url=os.getenv("DEEPSEEK_BASE_URL", DEEPSEEK_BASE_URL),
        temperature=0.2,
        max_tokens=2048,
        timeout=90,
        max_retries=2,
    )


_BUILDERS: dict[str, Callable[[], BaseChatModel | None]] = {
    "anthropic": _build_anthropic,
    "openai": _build_openai,
    "deepseek": _build_deepseek,
}


def _ordered_providers() -> list[str]:
    """Return PROVIDER_INDEX rotated so that the env-selected provider is first."""
    raw = os.getenv("PREPULSE_API_PROVIDER", "0").strip()
    try:
        idx = int(raw)
    except ValueError:
        # allow naming the provider directly e.g. PREPULSE_API_PROVIDER=deepseek
        if raw.lower() in PROVIDER_INDEX:
            idx = PROVIDER_INDEX.index(raw.lower())
        else:
            idx = 0
    idx = max(0, min(idx, len(PROVIDER_INDEX) - 1))
    chosen = PROVIDER_INDEX[idx]
    return [chosen] + [p for p in PROVIDER_INDEX if p != chosen]


def available_providers() -> list[str]:
    """Return the names of providers whose keys are present, in priority order."""
    out: list[str] = []
    for name in _ordered_providers():
        if _BUILDERS[name]() is not None:
            out.append(name)
    return out


def get_llm(tier: str = "primary") -> BaseChatModel:
    """Return an LLM with auto-fallback to other configured providers.

    `tier` is kept for backward compatibility with the old signature; it
    is no longer used to switch between primary and a hardcoded fallback —
    the chain itself encodes the fallback order.
    """
    chain: list[BaseChatModel] = []
    seen_names: list[str] = []
    for name in _ordered_providers():
        llm = _BUILDERS[name]()
        if llm is not None:
            chain.append(llm)
            seen_names.append(name)

    if not chain:
        raise RuntimeError(
            "No LLM provider configured. Set at least one of "
            "ANTHROPIC_API_KEY, OPENAI_API_KEY, or DEEPSEEK_API_KEY."
        )

    primary = chain[0]
    fallbacks = chain[1:]
    if not fallbacks:
        return primary
    # with_fallbacks turns the primary into a Runnable that retries on
    # exception with each fallback in order. Works for both invoke and
    # ainvoke and preserves bind_tools / structured-output behaviour.
    return primary.with_fallbacks(fallbacks)


def have_openai_fallback() -> bool:
    """Backwards-compat helper kept for any external callers."""
    return bool(os.getenv("OPENAI_API_KEY"))
