"""Scoring engine — branch-coverage tests over compute_posture_score()."""

from __future__ import annotations

from datetime import datetime

from backend.models.schemas import (
    BreachRecord,
    CVEFinding,
    HardeningAction,
    HardeningReport,
    IntelligenceReport,
    IPReputation,
    MitreTechnique,
    ThreatCampaign,
    ValidationReport,
)
from backend.services.scoring import WEIGHTS, compute_posture_score


def _intel(
    *,
    campaigns: int = 0,
    breached: bool = False,
    breach_count: int = 0,
    abuse_ips: int = 0,
) -> IntelligenceReport:
    return IntelligenceReport(
        domain="example.test",
        active_campaigns=[
            ThreatCampaign(
                pulse_id=f"p{i}",
                title="x",
                description="x",
                threat_level=3,
                industry_targeted="fintech",
                tags=[],
                first_seen="2026-01-01",
            )
            for i in range(campaigns)
        ],
        domain_breached=breached,
        breach_count=breach_count,
        breaches=[
            BreachRecord(
                breach_name="b",
                date="2020-01-01",
                pwn_count=1,
                data_classes=["Email"],
            )
            for _ in range(breach_count)
        ]
        if breached
        else [],
        suspicious_ips=[
            IPReputation(ip=f"10.0.0.{i}", abuse_confidence=90) for i in range(abuse_ips)
        ],
        raw_summary="",
        confidence=0.8,
    )


def _validation(cves: list[CVEFinding] | None = None) -> ValidationReport:
    return ValidationReport(
        cves_found=cves or [],
        mitre_techniques=[
            MitreTechnique(
                technique_id="T1190",
                technique_name="x",
                tactic="Initial Access",
                description="x",
                similarity_score=0.9,
            )
        ],
        exploitable_count=sum(1 for c in (cves or []) if c.exploit_available),
        validation_summary="",
        confidence=0.8,
    )


def _hardening(n_actions: int = 0) -> HardeningReport:
    return HardeningReport(
        actions_taken=[
            HardeningAction(
                action_id=f"a{i}",
                kind="mtd_port_rotation",
                description="x",
                target="t",
                executed_at=datetime.utcnow(),
                expected_impact="low",
            )
            for i in range(n_actions)
        ],
        rationale="",
        risk_reduction_estimate=2 * n_actions,
    )


def _cve(severity: str, exploit: bool = False) -> CVEFinding:
    return CVEFinding(
        cve_id=f"CVE-TEST-{severity}",
        severity=severity,  # type: ignore[arg-type]
        cvss_score=9.0 if severity == "CRITICAL" else 7.0,
        description="x",
        affected_product="x",
        exploit_available=exploit,
        published="2025-01-01",
    )


def test_perfect_clean_scan_gets_bonus_and_grade_A_or_B():
    intel = _intel(campaigns=0, breached=False)
    score, steps, grade = compute_posture_score(intel, _validation([]), _hardening(0))
    assert score == 100 + WEIGHTS["clean_intel_bonus"] - 5 or score == 100
    assert score <= 100
    assert grade in ("A", "B")
    assert any("clean intelligence posture" in s for s in steps)


def test_critical_cve_with_exploit_deducts_heavy():
    intel = _intel()
    validation = _validation([_cve("CRITICAL", exploit=True)])
    score, steps, _ = compute_posture_score(intel, validation, _hardening(0))
    assert score < 100
    assert any("exploit available" in s for s in steps)
    assert any("CRITICAL" in s for s in steps)


def test_breach_deducts_15():
    intel = _intel(breached=True, breach_count=1)
    baseline_score, _, _ = compute_posture_score(_intel(), _validation([]), _hardening(0))
    breached_score, _, _ = compute_posture_score(intel, _validation([]), _hardening(0))
    # breach removes 15 AND kills the clean-intel bonus, so delta is at least 15
    assert baseline_score - breached_score >= WEIGHTS["breach"]


def test_three_or_more_campaigns_triggers_volume_penalty():
    intel = _intel(campaigns=3)
    score, steps, _ = compute_posture_score(intel, _validation([]), _hardening(0))
    assert any("active campaigns" in s for s in steps)
    assert score < 100


def test_high_confidence_abuse_ip_deducts_per_ip():
    intel = _intel(abuse_ips=2)
    score, steps, _ = compute_posture_score(intel, _validation([]), _hardening(0))
    ip_steps = [s for s in steps if "abuse IP" in s]
    assert len(ip_steps) == 2


def test_hardening_actions_add_credit():
    intel = _intel()
    validation = _validation([])
    score_no_hardening, _, _ = compute_posture_score(intel, validation, _hardening(0))
    score_hardened, steps, _ = compute_posture_score(intel, validation, _hardening(3))
    expected_credit = 3 * WEIGHTS["hardening_credit_per_action"]
    # Both hit the 100 ceiling if the base is already 100, so credit is observable only
    # when base < 100 OR via the explicit "hardening credit" step
    assert any("hardening credit" in s for s in steps)
    assert score_hardened >= score_no_hardening
    assert score_hardened <= 100


def test_score_clamped_to_zero_floor():
    intel = _intel(campaigns=5, breached=True, breach_count=3, abuse_ips=4)
    validation = _validation(
        [_cve("CRITICAL", exploit=True) for _ in range(5)]
        + [_cve("HIGH", exploit=True) for _ in range(5)]
    )
    score, _, grade = compute_posture_score(intel, validation, _hardening(0))
    assert score == 0
    assert grade == "F"


def test_grade_mapping_covers_all_bands():
    def _score_for(deductions: int) -> tuple[int, str]:
        # no cves; fake out the score by using n CVE_LOW deductions
        cves = [_cve("LOW") for _ in range(deductions)]
        s, _, g = compute_posture_score(_intel(), _validation(cves), _hardening(0))
        return s, g

    a_score, a_grade = _score_for(5)  # 100+5-5=100 → A
    b_score, b_grade = _score_for(20)  # 100+5-20=85 → B
    c_score, c_grade = _score_for(35)  # 100+5-35=70 → C
    d_score, d_grade = _score_for(55)  # 100+5-55=50 → D
    f_score, f_grade = _score_for(80)  # → F
    assert a_grade == "A" and a_score >= 90
    assert b_grade == "B" and 75 <= b_score < 90
    assert c_grade == "C" and 60 <= c_score < 75
    assert d_grade == "D" and 40 <= d_score < 60
    assert f_grade == "F" and f_score < 40
