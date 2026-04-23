import asyncio
import time
import uuid

from backend.services.audit import record_action
from backend.tools.base import tool


@tool(name="email.notify_admin", category="action")
async def notify_admin(subject: str, body: str) -> dict:
    """Simulate sending an email notification to the admin distribution list."""
    await asyncio.sleep(0.1)
    msg_id = f"msg-{uuid.uuid4().hex[:8]}"
    record_action(
        {
            "action": "email.notify_admin",
            "message_id": msg_id,
            "subject": subject,
            "body_preview": body[:120],
            "ts": time.time(),
            "simulated": True,
        }
    )
    return {
        "message_id": msg_id,
        "sent": True,
        "subject": subject,
        "simulated": True,
        "message": f"Would email admins: {subject}",
    }
