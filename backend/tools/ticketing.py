import asyncio
import time
import uuid

from backend.services.audit import record_action
from backend.tools.base import tool


@tool(name="ticketing.open_incident", category="action")
async def open_incident(title: str, severity: str, details: str) -> dict:
    """Simulate opening an incident ticket in the ticketing system."""
    await asyncio.sleep(0.15)
    ticket_id = f"inc-{uuid.uuid4().hex[:6].upper()}"
    record_action(
        {
            "action": "ticketing.open_incident",
            "ticket_id": ticket_id,
            "title": title,
            "severity": severity,
            "details": details,
            "ts": time.time(),
            "simulated": True,
        }
    )
    return {
        "ticket_id": ticket_id,
        "opened": True,
        "severity": severity,
        "title": title,
        "simulated": True,
        "message": f"Would open incident {ticket_id} ({severity}): {title}",
    }
