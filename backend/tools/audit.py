import time
import uuid

from backend.services.audit import record_decision
from backend.tools.base import tool


@tool(name="audit.log_decision", category="meta")
async def log_decision(summary: str, sign_off: str = "approved") -> dict:
    """Record the Supervisor's sign-off in the audit store and return the trail id.

    The scan identifier is emitted on the event bus via the tool wrapper; we do
    not require it as a functional argument here to keep the tool signature
    free of collisions with the wrapper's own `scan_id` kwarg.
    """
    trail_id = f"audit-{uuid.uuid4().hex[:10]}"
    record_decision(
        {
            "audit_trail_id": trail_id,
            "summary": summary,
            "sign_off": sign_off,
            "ts": time.time(),
        }
    )
    return {
        "audit_trail_id": trail_id,
        "sign_off": sign_off,
        "logged": True,
    }
