"""Shared helpers for in-process test modules.

Wraps the agent + scoring + safety surface so individual test modules
stay short. None of these helpers reach the network — agents call the
real LLM only inside the agent modules themselves, gated by `requires=llm`.
"""

from __future__ import annotations

import asyncio
import json
import os
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from validation.context import ROOT


def load_profile_json(profile_id: str) -> dict:
    path = ROOT / "backend" / "demo" / "profiles" / f"{profile_id}.json"
    return json.loads(path.read_text())


def all_profile_ids() -> list[str]:
    profiles_dir = ROOT / "backend" / "demo" / "profiles"
    return sorted(p.stem for p in profiles_dir.glob("*.json"))


def known_cve_ids_from_fixtures() -> set[str]:
    """Build a 'known-good' CVE set from the demo NVD fixtures.

    Used as ground truth for F-02 (no live NVD calls). Any CVE id an
    agent emits that is not in this set is treated as hallucinated.
    """
    out: set[str] = set()
    mocks = ROOT / "backend" / "demo" / "mocks"
    for nvd in mocks.rglob("*_nvd.json"):
        for entry in json.loads(nvd.read_text()):
            cve = entry.get("cve_id")
            if cve:
                out.add(cve.upper())
    return out


def known_mitre_ids_from_fixtures() -> set[str]:
    """Build a 'known-good' MITRE technique-id set from the demo fixtures."""
    out: set[str] = set()
    mocks = ROOT / "backend" / "demo" / "mocks"
    for mitre in mocks.rglob("*_mitre.json"):
        for entry in json.loads(mitre.read_text()):
            tid = entry.get("technique_id")
            if tid:
                out.add(tid.upper())
    return out


_CVE_RE = re.compile(r"\bCVE-\d{4}-\d{4,7}\b", re.IGNORECASE)
_MITRE_RE = re.compile(r"\bT\d{4}(?:\.\d{3})?\b")


def extract_cve_ids(*texts: str) -> set[str]:
    out: set[str] = set()
    for t in texts:
        if not t:
            continue
        for m in _CVE_RE.findall(t):
            out.add(m.upper())
    return out


def extract_mitre_ids(*texts: str) -> set[str]:
    out: set[str] = set()
    for t in texts:
        if not t:
            continue
        out.update(_MITRE_RE.findall(t))
    return out


def make_synthetic_intel_report():
    from backend.models.schemas import (
        BreachRecord,
        IntelligenceReport,
        IPReputation,
        ThreatCampaign,
    )

    return IntelligenceReport(
        domain="rivercity.fin",
        active_campaigns=[
            ThreatCampaign(
                pulse_id="syn-1",
                title="Banking trojan campaign",
                description="Synthetic phishing campaign for tests.",
                threat_level=4,
                industry_targeted="fintech",
                tags=["banking-trojan"],
                first_seen="2026-04-01T00:00:00Z",
            )
        ],
        domain_breached=True,
        breach_count=1,
        breaches=[BreachRecord(breach_name="Synthetic Breach", date="2023-01-01", pwn_count=1000, data_classes=["Email"])],
        suspicious_ips=[IPReputation(ip="198.51.100.23", abuse_confidence=80)],
        raw_summary="synthetic",
        confidence=0.85,
    )


def make_synthetic_validation_report():
    from backend.models.schemas import CVEFinding, MitreTechnique, ValidationReport

    return ValidationReport(
        cves_found=[
            CVEFinding(
                cve_id="CVE-2026-10234",
                severity="CRITICAL",
                cvss_score=9.8,
                description="synthetic",
                affected_product="AWS Lambda",
                exploit_available=True,
                published="2026-04-02",
            )
        ],
        mitre_techniques=[
            MitreTechnique(
                technique_id="T1190",
                technique_name="Exploit Public-Facing Application",
                tactic="Initial Access",
                description="synthetic",
                similarity_score=0.91,
            )
        ],
        exploitable_count=1,
        validation_summary="synthetic",
        confidence=0.85,
    )


def make_synthetic_hardening_report():
    from backend.models.schemas import HardeningAction, HardeningReport

    return HardeningReport(
        actions_taken=[
            HardeningAction(
                action_id="h-1",
                kind="mtd_port_rotation",
                description="synthetic",
                target="edge",
                executed_at=datetime.utcnow(),
                expected_impact="recon invalidation",
            )
        ],
        rationale="synthetic",
        risk_reduction_estimate=4,
    )


def make_synthetic_final_report(score: int = 48):
    from backend.models.schemas import (
        CriticalFinding,
        FinalReport,
        RecommendedAction,
    )

    grade = "A" if score >= 90 else "B" if score >= 75 else "C" if score >= 60 else "D" if score >= 40 else "F"
    return FinalReport(
        posture_score=score,
        posture_grade=grade,
        score_explanation="synthetic",
        critical_findings=[CriticalFinding(headline="x", detail="x", linked_cves=["CVE-2026-10234"], linked_techniques=["T1190"], severity="critical")],
        recommended_actions=[RecommendedAction(priority=1, description="patch", estimated_effort="<1d", owner_suggestion="it_admin")],
        executive_summary="x",
        what_prepulse_would_do="x",
    )


def fresh_pipeline_state(profile_id: str):
    """Build a PipelineState with only the profile populated, for agent-isolation tests."""
    from backend.models.schemas import CompanyProfile, PipelineState

    data = load_profile_json(profile_id)
    return PipelineState(
        scan_id=f"val-{profile_id}-{int(time.time() * 1000)}",
        started_at=datetime.utcnow(),
        profile=CompanyProfile.model_validate(data["profile"]),
    )


def force_mock_mode() -> None:
    os.environ["PREPULSE_LIVE"] = "0"
    os.environ["PREPULSE_AUTO_APPROVE"] = "1"
    os.environ["PREPULSE_SKIP_SEED"] = "1"


def run_async(coro):
    """Sync wrapper used by `run(ctx)` callers (tests are sync-by-convention)."""
    return asyncio.get_event_loop().run_until_complete(coro) if asyncio.get_event_loop().is_running() else asyncio.run(coro)
