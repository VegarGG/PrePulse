import os

import requests

from backend.demo.mocks import mock_otx_pulses
from backend.tools.base import tool


@tool(
    name="otx.get_pulses",
    category="read",
    description="Return the N most recent threat campaigns matching the given industry.",
    input_schema={
        "type": "object",
        "properties": {
            "industry": {"type": "string"},
            "limit": {"type": "integer", "default": 5},
        },
        "required": ["industry"],
    },
)
async def get_pulses(industry: str, limit: int = 5) -> list[dict]:
    """Return the N most recent threat campaigns matching the given industry."""
    if os.getenv("PREPULSE_LIVE") != "1":
        return mock_otx_pulses(industry=industry, limit=limit)
    url = "https://otx.alienvault.com/api/v1/pulses/search"
    headers = {"X-OTX-API-KEY": os.environ["OTX_API_KEY"]}
    params = {"q": industry, "limit": limit, "sort": "-modified"}
    r = requests.get(url, headers=headers, params=params, timeout=10)
    r.raise_for_status()
    return [
        {
            "pulse_id": p.get("id"),
            "title": p.get("name"),
            "description": (p.get("description") or "")[:400],
            "threat_level": min(5, max(1, p.get("TLP", 3))),
            "industry_targeted": industry,
            "tags": p.get("tags", []),
            "first_seen": p.get("created", ""),
        }
        for p in r.json().get("results", [])
    ]
