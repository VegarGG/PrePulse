import os

import requests

from backend.demo.mocks import mock_abuseipdb_check_ip
from backend.tools.base import tool


@tool(
    name="abuseipdb.check_ip",
    category="read",
    description="Return reputation data for a single IP address.",
    input_schema={
        "type": "object",
        "properties": {
            "ip": {"type": "string"},
            "max_age_days": {"type": "integer", "default": 90},
        },
        "required": ["ip"],
    },
)
async def check_ip(ip: str, max_age_days: int = 90) -> dict:
    """Return reputation data for a single IP."""
    if os.getenv("PREPULSE_LIVE") != "1":
        return mock_abuseipdb_check_ip(ip=ip)
    url = "https://api.abuseipdb.com/api/v2/check"
    headers = {
        "Key": os.environ["ABUSEIPDB_API_KEY"],
        "Accept": "application/json",
    }
    params = {"ipAddress": ip, "maxAgeInDays": max_age_days}
    r = requests.get(url, headers=headers, params=params, timeout=10)
    r.raise_for_status()
    d = r.json().get("data", {})
    return {
        "ip": ip,
        "abuse_confidence": int(d.get("abuseConfidenceScore", 0)),
        "country": d.get("countryCode"),
        "usage_type": d.get("usageType"),
        "total_reports": int(d.get("totalReports", 0)),
    }
