import os

import requests

from backend.demo.mocks import mock_nvd_query_cves
from backend.tools.base import tool


@tool(
    name="nvd.query_cves",
    category="read",
    description="Return recent CVEs affecting the given product name.",
    input_schema={
        "type": "object",
        "properties": {
            "software": {"type": "string"},
            "limit": {"type": "integer", "default": 5},
        },
        "required": ["software"],
    },
)
async def query_cves(software: str, limit: int = 5) -> list[dict]:
    """Return recent CVEs affecting the given product."""
    if os.getenv("PREPULSE_LIVE") != "1":
        return mock_nvd_query_cves(software=software, limit=limit)
    url = "https://services.nvd.nist.gov/rest/json/cves/2.0"
    params = {"keywordSearch": software, "resultsPerPage": limit}
    headers = {"apiKey": os.environ["NVD_API_KEY"]} if os.getenv("NVD_API_KEY") else {}
    r = requests.get(url, params=params, headers=headers, timeout=15)
    r.raise_for_status()
    results: list[dict] = []
    for v in r.json().get("vulnerabilities", [])[:limit]:
        cve = v.get("cve", {})
        metrics = (cve.get("metrics") or {}).get("cvssMetricV31") or (
            cve.get("metrics") or {}
        ).get("cvssMetricV30") or []
        m = metrics[0] if metrics else {}
        base = (m.get("cvssData") or {}).get("baseScore")
        sev = (m.get("cvssData") or {}).get("baseSeverity", "MEDIUM")
        desc = ""
        for d in cve.get("descriptions", []):
            if d.get("lang") == "en":
                desc = d.get("value", "")
                break
        results.append(
            {
                "cve_id": cve.get("id", ""),
                "severity": sev.upper() if sev else "MEDIUM",
                "cvss_score": float(base) if base is not None else None,
                "description": desc[:500],
                "affected_product": software,
                "exploit_available": False,
                "published": cve.get("published", "")[:10],
            }
        )
    return results
