import asyncio
import time
from collections import defaultdict
from typing import Any

_subscribers: dict[str, list[asyncio.Queue]] = defaultdict(list)
_history: dict[str, list[dict]] = defaultdict(list)


async def emit(scan_id: str, event_type: str, payload: dict[str, Any]) -> None:
    evt = {"type": event_type, "ts": time.time(), "scan_id": scan_id, "payload": payload}
    _history[scan_id].append(evt)
    for q in _subscribers.get(scan_id, []):
        q.put_nowait(evt)


async def subscribe(scan_id: str) -> asyncio.Queue:
    q: asyncio.Queue = asyncio.Queue()
    for evt in _history.get(scan_id, []):
        q.put_nowait(evt)
    _subscribers[scan_id].append(q)
    return q


def unsubscribe(scan_id: str, q: asyncio.Queue) -> None:
    if q in _subscribers.get(scan_id, []):
        _subscribers[scan_id].remove(q)


def get_history(scan_id: str) -> list[dict]:
    return list(_history.get(scan_id, []))


def clear_history(scan_id: str | None = None) -> None:
    if scan_id is None:
        _history.clear()
    else:
        _history.pop(scan_id, None)
