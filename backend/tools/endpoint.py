import asyncio
import time
import uuid

from backend.services.audit import record_action
from backend.tools.base import tool


@tool(
    name="endpoint.isolate",
    category="action",
    description="Simulate isolating an endpoint from the network.",
    input_schema={
        "type": "object",
        "properties": {"host": {"type": "string"}},
        "required": ["host"],
    },
)
async def isolate(host: str) -> dict:
    """Simulate isolating an endpoint from the network."""
    await asyncio.sleep(0.15)
    iid = f"ep-{uuid.uuid4().hex[:8]}"
    record_action(
        {
            "action": "endpoint.isolate",
            "host": host,
            "isolation_id": iid,
            "ts": time.time(),
            "simulated": True,
        }
    )
    return {
        "host": host,
        "isolated": True,
        "isolation_id": iid,
        "simulated": True,
        "message": f"Would isolate host {host} from network",
    }


@tool(
    name="endpoint.quarantine_file",
    category="action",
    description="Simulate quarantining a suspicious file on an endpoint.",
    input_schema={
        "type": "object",
        "properties": {
            "host": {"type": "string"},
            "path": {"type": "string"},
        },
        "required": ["host", "path"],
    },
)
async def quarantine_file(host: str, path: str) -> dict:
    """Simulate quarantining a suspicious file on an endpoint."""
    await asyncio.sleep(0.15)
    qid = f"qf-{uuid.uuid4().hex[:8]}"
    record_action(
        {
            "action": "endpoint.quarantine_file",
            "host": host,
            "path": path,
            "quarantine_id": qid,
            "ts": time.time(),
            "simulated": True,
        }
    )
    return {
        "host": host,
        "path": path,
        "quarantined": True,
        "quarantine_id": qid,
        "simulated": True,
        "message": f"Would quarantine {path} on {host}",
    }
