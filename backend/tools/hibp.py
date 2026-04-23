import os

import requests

from backend.demo.mocks import mock_hibp_check_domain
from backend.tools.base import tool


@tool(
    name="hibp.check_domain",
    category="read",
    description="Return breach history for the given corporate domain.",
    input_schema={
        "type": "object",
        "properties": {"domain": {"type": "string"}},
        "required": ["domain"],
    },
)
async def check_domain(domain: str) -> dict:
    """Return breach history for the given corporate domain."""
    if os.getenv("PREPULSE_LIVE") != "1":
        return mock_hibp_check_domain(domain=domain)
    url = f"https://haveibeenpwned.com/api/v3/breaches?domain={domain}"
    headers = {
        "hibp-api-key": os.environ["HIBP_API_KEY"],
        "user-agent": "PrePulse/0.2",
    }
    r = requests.get(url, headers=headers, timeout=10)
    r.raise_for_status()
    breaches = [
        {
            "breach_name": b.get("Name", ""),
            "date": b.get("BreachDate", ""),
            "pwn_count": int(b.get("PwnCount", 0)),
            "data_classes": b.get("DataClasses", []),
        }
        for b in r.json()
    ]
    return {
        "domain": domain,
        "breached": bool(breaches),
        "breach_count": len(breaches),
        "breaches": breaches,
    }
