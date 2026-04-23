"""LLM gateway.

Primary model: claude-sonnet-4-6 via langchain-anthropic.
Optional fallback: gpt-4o via langchain-openai, used when Anthropic raises
RateLimitError / APIConnectionError or structured-output parsing fails twice.
Temperature fixed at 0.2 for reproducibility (§14.4).
"""

from __future__ import annotations

import os


def get_llm(tier: str = "primary"):
    if tier == "primary":
        from langchain_anthropic import ChatAnthropic

        return ChatAnthropic(
            model="claude-sonnet-4-6",
            temperature=0.2,
            max_tokens=2048,
            timeout=90,
            max_retries=2,
        )

    from langchain_openai import ChatOpenAI

    return ChatOpenAI(
        model="gpt-4o",
        temperature=0.2,
        max_tokens=2048,
        timeout=90,
        max_retries=2,
    )


def have_openai_fallback() -> bool:
    return bool(os.getenv("OPENAI_API_KEY"))
