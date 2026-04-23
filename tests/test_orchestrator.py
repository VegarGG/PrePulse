"""Agent-isolation tests — 6 agents × 3 profiles = 18.

Each test seeds a PipelineState populated up through the agent's inputs,
runs the agent, and asserts (1) the returned report is the expected Pydantic
type and (2) each agent's mandatory tool set shows up in the event bus.

These tests make real LLM calls. Skipped if ANTHROPIC_API_KEY is not set.
"""

from __future__ import annotations

import json
import os
import uuid
from datetime import datetime
from pathlib import Path

import pytest
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

from backend.agents import (
    hardening as hardening_agent,
    intelligence as intelligence_agent,
    investigator as investigator_agent,
    remediator as remediator_agent,
    supervisor as supervisor_agent,
    validator as validator_agent,
)
from backend.events import clear_history, get_history
from backend.models.schemas import (
    BreachRecord,
    CompanyProfile,
    CriticalFinding,
    CVEFinding,
    FinalReport,
    HardeningAction,
    HardeningReport,
    IntelligenceReport,
    IPReputation,
    MitreTechnique,
    PipelineState,
    RecommendedAction,
    RemediationAction,
    RemediationReport,
    SupervisorReport,
    ThreatCampaign,
    ValidationReport,
)

REQUIRES_KEY = pytest.mark.skipif(
    not os.getenv("ANTHROPIC_API_KEY"),
    reason="ANTHROPIC_API_KEY not set — skipping live LLM tests",
)


PROFILES_DIR = Path(__file__).resolve().parents[1] / "backend" / "demo" / "profiles"


def _load_profile(profile_id: str) -> CompanyProfile:
    data = json.loads((PROFILES_DIR / f"{profile_id}.json").read_text())
    return CompanyProfile.model_validate(data["profile"])


def _synthetic_intel(profile: CompanyProfile) -> IntelligenceReport:
    breached = profile.industry != "e-commerce"
    return IntelligenceReport(
        domain=profile.domain,
        active_campaigns=[
            ThreatCampaign(
                pulse_id="syn-1",
                title=f"Active campaign targeting {profile.industry}",
                description=f"Synthetic campaign for {profile.industry} tests.",
                threat_level=4,
                industry_targeted=profile.industry,
                tags=["synthetic", profile.industry],
                first_seen="2026-04-10T00:00:00Z",
            ),
            ThreatCampaign(
                pulse_id="syn-2",
                title="Credential-harvesting phishing wave",
                description="Generic phishing wave observed across industry.",
                threat_level=3,
                industry_targeted=profile.industry,
                tags=["phishing"],
                first_seen="2026-04-12T00:00:00Z",
            ),
        ],
        domain_breached=breached,
        breach_count=1 if breached else 0,
        breaches=[
            BreachRecord(
                breach_name="SyntheticBreach 2023",
                date="2023-06-01",
                pwn_count=123456,
                data_classes=["Email addresses", "Passwords"],
            )
        ]
        if breached
        else [],
        suspicious_ips=[
            IPReputation(
                ip="198.51.100.23",
                abuse_confidence=82,
                country="US",
                usage_type="Data Center",
                total_reports=17,
            )
        ],
        raw_summary=f"Synthetic intel summary for {profile.company_name}.",
        confidence=0.82,
    )


def _synthetic_validation(profile: CompanyProfile) -> ValidationReport:
    product = profile.tech_stack[0] if profile.tech_stack else "Generic Product"
    return ValidationReport(
        cves_found=[
            CVEFinding(
                cve_id="CVE-2026-10234",
                severity="CRITICAL",
                cvss_score=9.8,
                description="Synthetic critical vulnerability used for testing.",
                affected_product=product,
                exploit_available=True,
                published="2026-04-02",
            ),
            CVEFinding(
                cve_id="CVE-2025-49112",
                severity="HIGH",
                cvss_score=8.1,
                description="Synthetic high-severity vulnerability.",
                affected_product=product,
                exploit_available=False,
                published="2025-12-15",
            ),
        ],
        mitre_techniques=[
            MitreTechnique(
                technique_id="T1190",
                technique_name="Exploit Public-Facing Application",
                tactic="Initial Access",
                description="Adversaries exploit weaknesses in internet-facing applications.",
                similarity_score=0.91,
            ),
            MitreTechnique(
                technique_id="T1566.001",
                technique_name="Spearphishing Attachment",
                tactic="Initial Access",
                description="Adversaries send emails with a malicious attachment.",
                similarity_score=0.85,
            ),
        ],
        exploitable_count=1,
        validation_summary="Synthetic validation summary for tests.",
        confidence=0.80,
    )


def _synthetic_hardening() -> HardeningReport:
    return HardeningReport(
        actions_taken=[
            HardeningAction(
                action_id="h-1",
                kind="mtd_port_rotation",
                description="Rotated exposed service ports",
                target="edge-gateway",
                executed_at=datetime.utcnow(),
                expected_impact="Recon invalidation",
            )
        ],
        rationale="Preemptive port rotation to invalidate attacker recon.",
        risk_reduction_estimate=4,
    )


def _synthetic_final(profile: CompanyProfile) -> FinalReport:
    # deliberately pick a D-grade score so the report is non-trivial
    return FinalReport(
        posture_score=48,
        posture_grade="D",
        score_explanation="Synthetic score breakdown for tests.",
        critical_findings=[
            CriticalFinding(
                headline=f"Exploitable {profile.tech_stack[0] if profile.tech_stack else 'app'} CVE",
                detail="Synthetic critical finding used in tests.",
                linked_cves=["CVE-2026-10234"],
                linked_techniques=["T1190"],
                severity="critical",
            )
        ],
        recommended_actions=[
            RecommendedAction(
                priority=1,
                description="Patch the critical CVE immediately.",
                estimated_effort="<1d",
                owner_suggestion="it_admin",
            )
        ],
        executive_summary=(
            f"{profile.company_name} has a serious exposure that a small team of attackers "
            "could exploit within a day. PrePulse has already rotated some attack surface "
            "and recommends immediate remediation of the flagged vulnerability."
        ),
        what_prepulse_would_do=(
            "In production PrePulse would auto-block known-bad IPs, patch the vulnerable "
            "service in a canary, and force MFA rotation on affected identities."
        ),
    )


def _synthetic_remediation() -> RemediationReport:
    return RemediationReport(
        actions=[
            RemediationAction(
                action_id="r-1",
                kind="firewall.block_ip",
                severity="high",
                args={"ip": "198.51.100.23", "reason": "C2", "duration_hours": 24},
                requires_approval=True,
            ),
            RemediationAction(
                action_id="r-2",
                kind="ticketing.open_incident",
                severity="medium",
                args={"title": "Investigate exposure", "severity": "medium", "details": "..."},
                requires_approval=False,
            ),
        ],
        actions_approved=0,
        actions_executed=0,
        actions_rejected=0,
    )


def _fresh_state(profile: CompanyProfile, scan_id: str) -> PipelineState:
    return PipelineState(
        scan_id=scan_id,
        started_at=datetime.utcnow(),
        profile=profile,
    )


def _state_for(agent_name: str, profile: CompanyProfile, scan_id: str) -> PipelineState:
    """Build a state seeded up through the dependencies of `agent_name`."""
    state = _fresh_state(profile, scan_id)
    if agent_name == "intelligence":
        return state
    intel = _synthetic_intel(profile)
    state = state.model_copy(update={"intel_report": intel})
    if agent_name == "validator":
        return state
    validation = _synthetic_validation(profile)
    state = state.model_copy(update={"validation_report": validation})
    if agent_name == "hardening":
        return state
    hardening = _synthetic_hardening()
    state = state.model_copy(update={"hardening_report": hardening})
    if agent_name == "investigator":
        return state
    final = _synthetic_final(profile)
    state = state.model_copy(update={"final_report": final})
    if agent_name == "remediator":
        return state
    state = state.model_copy(update={"remediation_report": _synthetic_remediation()})
    return state


AGENT_SPECS = [
    (
        "intelligence",
        intelligence_agent,
        "intel_report",
        IntelligenceReport,
        # intelligence must call at least one of its read tools
        {"mandatory_any": [{"otx.get_pulses", "hibp.check_domain", "abuseipdb.check_ip"}]},
    ),
    (
        "validator",
        validator_agent,
        "validation_report",
        ValidationReport,
        {"mandatory_any": [{"nvd.query_cves", "mitre.match_techniques"}]},
    ),
    (
        "hardening",
        hardening_agent,
        "hardening_report",
        HardeningReport,
        # hardening must call at least one of the action tools it is allowed
        {"mandatory_any": [{"mtd.rotate_port_map", "mtd.refresh_certs", "iam.rotate_credentials"}]},
    ),
    (
        "investigator",
        investigator_agent,
        "final_report",
        FinalReport,
        {"mandatory_any": []},  # reasoning-only
    ),
    (
        "remediator",
        remediator_agent,
        "remediation_report",
        RemediationReport,
        {"mandatory_any": []},  # planning-only
    ),
    (
        "supervisor",
        supervisor_agent,
        "supervisor_report",
        SupervisorReport,
        {"mandatory_any": [{"policy.check"}, {"audit.log_decision"}]},
    ),
]


@REQUIRES_KEY
@pytest.mark.parametrize("profile_id", ["river_city", "greenfield", "shoplocal"])
@pytest.mark.parametrize(
    "agent_name,agent_module,field,schema,tool_assertion",
    AGENT_SPECS,
    ids=[s[0] for s in AGENT_SPECS],
)
async def test_agent_in_isolation(
    profile_id, agent_name, agent_module, field, schema, tool_assertion
):
    profile = _load_profile(profile_id)
    scan_id = f"s-{agent_name}-{profile_id}-{uuid.uuid4().hex[:6]}"
    clear_history(scan_id)

    state = _state_for(agent_name, profile, scan_id)
    new_state = await agent_module.run(state)

    report = getattr(new_state, field)
    assert report is not None, f"{agent_name}.run left {field} unset"
    assert isinstance(report, schema), (
        f"{agent_name}.run returned {type(report).__name__} but expected {schema.__name__}"
    )

    # Re-validate through the Pydantic serializer as a belt-and-braces check.
    schema.model_validate(report.model_dump())

    events = get_history(scan_id)
    types = [e["type"] for e in events]
    assert "agent.started" in types
    assert "agent.completed" in types

    tools_called = {
        e["payload"]["tool"]
        for e in events
        if e["type"] == "tool.called"
    }

    for required_group in tool_assertion["mandatory_any"]:
        assert tools_called & required_group, (
            f"{agent_name} on {profile_id}: expected any of {required_group} to be called; "
            f"got {tools_called}"
        )
