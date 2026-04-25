"""InputValidator — prompt-injection defense on user-supplied profile fields."""

from __future__ import annotations

import re

from fastapi import HTTPException

from backend.models.schemas import CompanyProfile

_INJECTION_PATTERNS = [
    re.compile(r"ignore (all )?(previous|prior) instructions", re.IGNORECASE),
    re.compile(r"disregard (the )?system (prompt|message)", re.IGNORECASE),
    re.compile(r"reveal (your|the) system prompt", re.IGNORECASE),
    re.compile(r"you are now", re.IGNORECASE),
    re.compile(r"act as (?!a security analyst)", re.IGNORECASE),
    re.compile(r"<\|im_start\|>|<\|im_end\|>"),
]


def validate_profile(profile: CompanyProfile) -> None:
    fields = [profile.company_name, profile.domain] + list(profile.tech_stack)
    for field in fields:
        if not isinstance(field, str):
            continue
        for pat in _INJECTION_PATTERNS:
            if pat.search(field):
                raise HTTPException(
                    status_code=400,
                    detail={
                        "error": "input_validation_failed",
                        "reason": "prompt_injection_suspected",
                        "field": field[:60],
                    },
                )


def check_chat_input(message: str) -> None:
    """Lightweight prompt-injection check for free-form chat input.

    The chatbot system prompt is the primary guardrail (it scopes the model
    and demands structured output), but flagging obvious jailbreaks here
    short-circuits the LLM call entirely.
    """
    if not isinstance(message, str):
        raise HTTPException(400, {"error": "invalid_message", "reason": "must be a string"})
    if len(message) > 2000:
        raise HTTPException(
            400,
            {"error": "message_too_long", "reason": "max 2000 characters"},
        )
    for pat in _INJECTION_PATTERNS:
        if pat.search(message):
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "input_validation_failed",
                    "reason": "prompt_injection_suspected",
                    "preview": message[:80],
                },
            )
