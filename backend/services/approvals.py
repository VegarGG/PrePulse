"""Human-in-the-loop approval registry.

The Remediator awaits on a future keyed by (scan_id, action_id). The API
layer resolves that future when the user clicks Approve or Reject.
"""

from __future__ import annotations

import asyncio

_pending: dict[tuple[str, str], asyncio.Future] = {}


def register_pending(scan_id: str, action_id: str) -> asyncio.Future:
    loop = asyncio.get_event_loop()
    fut: asyncio.Future = loop.create_future()
    _pending[(scan_id, action_id)] = fut
    return fut


async def await_approval(
    scan_id: str, action_id: str, timeout: float = 120.0
) -> bool:
    """Block until an operator approves or rejects the action. Timeout → False."""
    key = (scan_id, action_id)
    fut = _pending.get(key)
    if fut is None:
        fut = register_pending(scan_id, action_id)
    try:
        return bool(await asyncio.wait_for(fut, timeout=timeout))
    except asyncio.TimeoutError:
        return False
    finally:
        _pending.pop(key, None)


def resolve_approval(scan_id: str, action_id: str, approved: bool) -> bool:
    """Return True if a pending future was resolved, False if nothing was pending."""
    fut = _pending.get((scan_id, action_id))
    if fut is None or fut.done():
        return False
    fut.set_result(approved)
    return True


def has_pending(scan_id: str, action_id: str) -> bool:
    fut = _pending.get((scan_id, action_id))
    return fut is not None and not fut.done()


def clear() -> None:
    _pending.clear()
