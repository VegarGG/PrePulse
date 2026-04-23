import asyncio
import time
import uuid

from backend.services.audit import record_action
from backend.tools.base import tool


@tool(
    name="firewall.block_ip",
    category="action",
    description="Simulate blocking an IP at the perimeter firewall.",
    input_schema={
        "type": "object",
        "properties": {
            "ip": {"type": "string"},
            "reason": {"type": "string"},
            "duration_hours": {"type": "integer", "default": 24},
        },
        "required": ["ip", "reason"],
    },
)
async def block_ip(ip: str, reason: str, duration_hours: int = 24) -> dict:
    """Simulate blocking an IP at the perimeter firewall."""
    await asyncio.sleep(0.2)
    rule_id = f"fw-{uuid.uuid4().hex[:8]}"
    record_action(
        {
            "action": "firewall.block_ip",
            "ip": ip,
            "reason": reason,
            "duration_hours": duration_hours,
            "rule_id": rule_id,
            "ts": time.time(),
            "simulated": True,
        }
    )
    return {
        "rule_id": rule_id,
        "ip": ip,
        "blocked": True,
        "simulated": True,
        "message": f"Would block {ip} at perimeter for {duration_hours}h",
    }


@tool(
    name="firewall.block_range",
    category="action",
    description="Simulate blocking a CIDR range at the perimeter.",
    input_schema={
        "type": "object",
        "properties": {
            "cidr": {"type": "string"},
            "reason": {"type": "string"},
            "duration_hours": {"type": "integer", "default": 24},
        },
        "required": ["cidr", "reason"],
    },
)
async def block_range(cidr: str, reason: str, duration_hours: int = 24) -> dict:
    """Simulate blocking an entire CIDR range."""
    await asyncio.sleep(0.2)
    rule_id = f"fw-{uuid.uuid4().hex[:8]}"
    record_action(
        {
            "action": "firewall.block_range",
            "cidr": cidr,
            "reason": reason,
            "duration_hours": duration_hours,
            "rule_id": rule_id,
            "ts": time.time(),
            "simulated": True,
        }
    )
    return {
        "rule_id": rule_id,
        "cidr": cidr,
        "blocked": True,
        "simulated": True,
        "message": f"Would block {cidr} at perimeter for {duration_hours}h",
    }
