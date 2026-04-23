"""Tool registry + decorator.

Every tool registers itself under a dotted name (`otx.get_pulses`). The
decorator additionally captures a human-readable `description` and a JSON
Schema (`input_schema`) so agents can bind tools to the LLM without
maintaining a parallel lookup table — the registry is the single source of
truth for both dispatch and LLM-facing metadata.

The wrapper emits `tool.called` and `tool.result` events before and after
invocation. The active agent's name is pulled from a contextvar so events
are always attributed correctly; `BaseAgent.run_core()` sets that contextvar
for the duration of its LLM loop.
"""

from __future__ import annotations

import os
import time
import uuid
from contextvars import ContextVar
from functools import wraps
from typing import Any, Callable, Literal

from backend.events import emit

TOOLS: dict[str, Callable[..., Any]] = {}

# The agent currently executing. Set by BaseAgent._run_llm_loop so every tool
# call emitted inside that context is attributed to the right lane.
_current_agent: ContextVar[str | None] = ContextVar("prepulse_current_agent", default=None)


def set_current_agent(name: str | None) -> Any:
    """Set the active agent name; returns a token to pass to reset_current_agent."""
    return _current_agent.set(name)


def reset_current_agent(token: Any) -> None:
    _current_agent.reset(token)


def _dotted_to_alias(name: str) -> str:
    """`foo.bar_baz` → `foo_bar_baz` (first dot only, Anthropic-safe)."""
    return name.replace(".", "_", 1)


def tool(
    *,
    name: str,
    category: Literal["read", "action", "meta"],
    description: str = "",
    input_schema: dict | None = None,
):
    schema = input_schema or {"type": "object", "properties": {}}

    def decorator(fn):
        @wraps(fn)
        async def wrapper(scan_id: str, **kwargs):
            call_id = f"t-{uuid.uuid4().hex[:6]}"
            agent = _current_agent.get()
            await emit(
                scan_id,
                "tool.called",
                {
                    "call_id": call_id,
                    "tool": name,
                    "category": category,
                    "agent": agent,
                    "args": kwargs,
                    "mode": "live" if os.getenv("PREPULSE_LIVE") == "1" else "mock",
                },
            )
            t0 = time.perf_counter()
            try:
                result = await fn(**kwargs)
                await emit(
                    scan_id,
                    "tool.result",
                    {
                        "call_id": call_id,
                        "tool": name,
                        "agent": agent,
                        "duration_ms": int((time.perf_counter() - t0) * 1000),
                        "result": result,
                        "ok": True,
                    },
                )
                return result
            except Exception as e:
                await emit(
                    scan_id,
                    "tool.result",
                    {
                        "call_id": call_id,
                        "tool": name,
                        "agent": agent,
                        "ok": False,
                        "error": str(e),
                    },
                )
                raise

        TOOLS[name] = wrapper
        wrapper._tool_meta = {  # type: ignore[attr-defined]
            "name": name,
            "alias": _dotted_to_alias(name),
            "category": category,
            "description": description or (fn.__doc__ or "").strip().split("\n")[0],
            "input_schema": schema,
        }
        return wrapper

    return decorator
