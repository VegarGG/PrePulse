"""Scripted mock responses for the five read tools.

Dispatch keyed by tool input where possible (industry, domain, ip). For inputs
that don't uniquely identify a profile (threat descriptions, software names)
we scan all three profiles and return the best match.
"""

from __future__ import annotations

import json
from functools import lru_cache
from ipaddress import ip_address, ip_network
from pathlib import Path
from typing import Any

_ROOT = Path(__file__).parent
_PROFILES = ("river_city", "greenfield", "shoplocal")

INDUSTRY_TO_PROFILE = {
    "fintech": "river_city",
    "healthcare": "greenfield",
    "e-commerce": "shoplocal",
}

DOMAIN_TO_PROFILE = {
    "rivercity.fin": "river_city",
    "greenfieldclinic.health": "greenfield",
    "shoplocal.market": "shoplocal",
}

IP_RANGE_TO_PROFILE = {
    "198.51.100.0/24": "river_city",
    "203.0.113.0/24": "greenfield",
    "192.0.2.0/24": "shoplocal",
}


@lru_cache(maxsize=32)
def _load(profile: str, fname: str) -> Any:
    path = _ROOT / profile / fname
    if not path.exists():
        return None
    return json.loads(path.read_text())


def _profile_for_ip(ip: str) -> str | None:
    # exact-match fixture first
    for p in _PROFILES:
        data = _load(p, f"{p}_abuse.json")
        if data and data.get("ip") == ip:
            return p
    # fall back to CIDR membership so any ip the LLM probes within a profile's
    # declared range still returns that profile's reputation data
    try:
        addr = ip_address(ip)
    except ValueError:
        return None
    for cidr, p in IP_RANGE_TO_PROFILE.items():
        if addr in ip_network(cidr):
            return p
    return None


def mock_otx_pulses(industry: str, limit: int = 5) -> list[dict]:
    profile = INDUSTRY_TO_PROFILE.get(industry.lower(), "shoplocal")
    data = _load(profile, f"{profile}_pulses.json") or []
    return data[:limit]


def mock_hibp_check_domain(domain: str) -> dict:
    profile = DOMAIN_TO_PROFILE.get(domain.lower())
    if profile is None:
        return {"domain": domain, "breached": False, "breach_count": 0, "breaches": []}
    return _load(profile, f"{profile}_hibp.json") or {
        "domain": domain,
        "breached": False,
        "breach_count": 0,
        "breaches": [],
    }


def mock_abuseipdb_check_ip(ip: str) -> dict:
    profile = _profile_for_ip(ip)
    if profile:
        data = _load(profile, f"{profile}_abuse.json")
        if data:
            return {**data, "ip": ip}
    return {
        "ip": ip,
        "abuse_confidence": 0,
        "country": None,
        "usage_type": None,
        "total_reports": 0,
    }


def mock_nvd_query_cves(software: str, limit: int = 5) -> list[dict]:
    needle = software.lower().strip()
    for p in _PROFILES:
        data = _load(p, f"{p}_nvd.json") or []
        matches = [
            c for c in data if needle in (c.get("affected_product", "").lower())
        ]
        if matches:
            return matches[:limit]
    return []


_MITRE_KEYWORDS = {
    "river_city": (
        "bank",
        "fintech",
        "stripe",
        "grandoreiro",
        "lambda",
        "trojan",
        "magecart",
    ),
    "greenfield": (
        "health",
        "ransomware",
        "exchange",
        "clinic",
        "phi",
        "ehr",
        "blackbasta",
    ),
    "shoplocal": (
        "shop",
        "ecommerce",
        "e-commerce",
        "skimmer",
        "shopify",
        "storefront",
    ),
}


def mock_mitre_match_techniques(threat_description: str, k: int = 3) -> list[dict]:
    desc = (threat_description or "").lower()
    best_profile = "river_city"
    best_hits = 0
    for profile, keywords in _MITRE_KEYWORDS.items():
        hits = sum(1 for kw in keywords if kw in desc)
        if hits > best_hits:
            best_hits = hits
            best_profile = profile
    data = _load(best_profile, f"{best_profile}_mitre.json") or []
    return data[:k]
