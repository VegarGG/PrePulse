"""Tool registry tests.

For every tool (read + action + meta), verify the mock path returns a shape
matching its declared Pydantic schema where applicable. Read tools are
parametrized by profile (§20). Action and meta tools are exercised once per
tool with a representative payload.
"""

from __future__ import annotations

import pytest

from backend.models.schemas import (
    BreachRecord,
    CVEFinding,
    IPReputation,
    MitreTechnique,
    ThreatCampaign,
)
from backend.tools import TOOLS  # noqa: F401  — populates registry
from backend.tools import abuseipdb, audit, email, endpoint, firewall
from backend.tools import hibp, iam, mitre, mtd, nvd, otx, policy, ticketing


PROFILE_INPUTS = [
    {
        "profile_id": "river_city",
        "industry": "fintech",
        "domain": "rivercity.fin",
        "ip": "198.51.100.23",
        "software": "AWS Lambda",
        "threat_desc": "banking trojan grandoreiro phishing fintech",
        "expects_breach": True,
        "expects_high_abuse": True,
        "expects_cves": True,
    },
    {
        "profile_id": "greenfield",
        "industry": "healthcare",
        "domain": "greenfieldclinic.health",
        "ip": "203.0.113.45",
        "software": "Microsoft Exchange 2019",
        "threat_desc": "ransomware blackbasta exchange healthcare clinic",
        "expects_breach": True,
        "expects_high_abuse": True,
        "expects_cves": True,
    },
    {
        "profile_id": "shoplocal",
        "industry": "e-commerce",
        "domain": "shoplocal.market",
        "ip": "192.0.2.10",
        "software": "MySQL",
        "threat_desc": "ecommerce skimmer shopify storefront",
        "expects_breach": False,
        "expects_high_abuse": False,
        "expects_cves": True,
    },
]


# ---------- otx.get_pulses ----------


@pytest.mark.parametrize("p", PROFILE_INPUTS, ids=[p["profile_id"] for p in PROFILE_INPUTS])
async def test_otx_get_pulses_returns_valid_campaigns(scan_id, p):
    result = await otx.get_pulses(scan_id, industry=p["industry"], limit=5)
    assert isinstance(result, list)
    assert len(result) >= 1
    for item in result:
        ThreatCampaign.model_validate(
            {
                **item,
                "industry_targeted": item.get("industry_targeted", p["industry"]),
            }
        )


# ---------- hibp.check_domain ----------


@pytest.mark.parametrize("p", PROFILE_INPUTS, ids=[p["profile_id"] for p in PROFILE_INPUTS])
async def test_hibp_check_domain_returns_typed_shape(scan_id, p):
    result = await hibp.check_domain(scan_id, domain=p["domain"])
    assert set(["domain", "breached", "breach_count", "breaches"]).issubset(result.keys())
    assert result["breached"] is p["expects_breach"]
    for b in result["breaches"]:
        BreachRecord.model_validate(b)


# ---------- abuseipdb.check_ip ----------


@pytest.mark.parametrize("p", PROFILE_INPUTS, ids=[p["profile_id"] for p in PROFILE_INPUTS])
async def test_abuseipdb_check_ip_returns_ipreputation(scan_id, p):
    result = await abuseipdb.check_ip(scan_id, ip=p["ip"])
    IPReputation.model_validate(result)
    if p["expects_high_abuse"]:
        assert result["abuse_confidence"] >= 75
    else:
        assert result["abuse_confidence"] < 25


# ---------- nvd.query_cves ----------


@pytest.mark.parametrize("p", PROFILE_INPUTS, ids=[p["profile_id"] for p in PROFILE_INPUTS])
async def test_nvd_query_cves_returns_list_of_cvefindings(scan_id, p):
    result = await nvd.query_cves(scan_id, software=p["software"], limit=5)
    assert isinstance(result, list)
    if p["expects_cves"]:
        assert len(result) >= 1
    for cve in result:
        CVEFinding.model_validate(cve)


# ---------- mitre.match_techniques ----------


@pytest.mark.parametrize("p", PROFILE_INPUTS, ids=[p["profile_id"] for p in PROFILE_INPUTS])
async def test_mitre_match_techniques_returns_typed_list(scan_id, p):
    result = await mitre.match_techniques(scan_id, threat_description=p["threat_desc"], k=3)
    assert isinstance(result, list)
    assert 1 <= len(result) <= 3
    for t in result:
        MitreTechnique.model_validate(t)


# ---------- Action tools (simulated) ----------


async def test_firewall_block_ip(scan_id):
    r = await firewall.block_ip(scan_id, ip="198.51.100.23", reason="test")
    assert r["blocked"] is True and r["simulated"] is True and r["ip"] == "198.51.100.23"


async def test_firewall_block_range(scan_id):
    r = await firewall.block_range(scan_id, cidr="198.51.100.0/24", reason="test")
    assert r["blocked"] is True and r["simulated"] is True


async def test_iam_force_mfa(scan_id):
    r = await iam.force_mfa(scan_id, scope="admins")
    assert r["mfa_enforced"] is True and r["scope"] == "admins"


async def test_iam_rotate_credentials(scan_id):
    r = await iam.rotate_credentials(scan_id, scope="service-accounts")
    assert r["rotated"] is True


async def test_iam_disable_user(scan_id):
    r = await iam.disable_user(scan_id, user="alice@example.test")
    assert r["disabled"] is True and r["user"] == "alice@example.test"


async def test_endpoint_isolate(scan_id):
    r = await endpoint.isolate(scan_id, host="ws-07")
    assert r["isolated"] is True and r["host"] == "ws-07"


async def test_endpoint_quarantine_file(scan_id):
    r = await endpoint.quarantine_file(scan_id, host="ws-07", path="/tmp/sus.exe")
    assert r["quarantined"] is True and r["path"] == "/tmp/sus.exe"


async def test_mtd_rotate_port_map(scan_id):
    r = await mtd.rotate_port_map(scan_id)
    assert r["rotated"] is True


async def test_mtd_refresh_certs(scan_id):
    r = await mtd.refresh_certs(scan_id)
    assert r["refreshed"] is True


async def test_ticketing_open_incident(scan_id):
    r = await ticketing.open_incident(
        scan_id, title="Lambda RCE observed", severity="critical", details="CVE-2026-10234"
    )
    assert r["opened"] is True and r["severity"] == "critical"
    assert r["ticket_id"].startswith("inc-")


async def test_email_notify_admin(scan_id):
    r = await email.notify_admin(
        scan_id, subject="Action taken", body="See incident inc-ABC123"
    )
    assert r["sent"] is True
    assert r["message_id"].startswith("msg-")


# ---------- Meta tools ----------


async def test_policy_check_allows_empty(scan_id):
    r = await policy.check(scan_id, action_list=[])
    assert r["ok"] is True and r["violations"] == []


async def test_policy_check_flags_ungated_high_severity(scan_id):
    actions = [{"kind": "firewall.block_ip", "severity": "high", "requires_approval": False}]
    r = await policy.check(scan_id, action_list=actions)
    assert r["ok"] is False and any("approval" in v for v in r["violations"])


async def test_audit_log_decision_returns_trail_id(scan_id):
    r = await audit.log_decision(scan_id, summary="All agents passed", sign_off="approved")
    assert r["logged"] is True
    assert r["audit_trail_id"].startswith("audit-")
    assert r["sign_off"] == "approved"


# ---------- Registry completeness ----------


def test_all_expected_tools_registered():
    expected = {
        "otx.get_pulses",
        "hibp.check_domain",
        "abuseipdb.check_ip",
        "nvd.query_cves",
        "mitre.match_techniques",
        "firewall.block_ip",
        "firewall.block_range",
        "iam.force_mfa",
        "iam.rotate_credentials",
        "iam.disable_user",
        "endpoint.isolate",
        "endpoint.quarantine_file",
        "mtd.rotate_port_map",
        "mtd.refresh_certs",
        "ticketing.open_incident",
        "email.notify_admin",
        "policy.check",
        "audit.log_decision",
    }
    assert expected.issubset(set(TOOLS.keys()))


def test_every_tool_has_metadata():
    for name, fn in TOOLS.items():
        meta = getattr(fn, "_tool_meta", None)
        assert meta is not None, f"{name} missing _tool_meta"
        assert meta["category"] in {"read", "action", "meta"}
        assert meta["name"] == name
