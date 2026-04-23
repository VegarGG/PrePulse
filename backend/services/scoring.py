from backend.models.schemas import HardeningReport, IntelligenceReport, ValidationReport

WEIGHTS = {
    "cve_critical": 10,
    "cve_high": 5,
    "cve_medium": 3,
    "cve_low": 1,
    "exploit_available_bonus": 3,
    "breach": 15,
    "active_campaigns_3plus": 10,
    "abuse_ip_high_confidence": 8,
    "hardening_credit_per_action": 2,
    "clean_intel_bonus": 5,
}


def compute_posture_score(
    intel: IntelligenceReport,
    validation: ValidationReport,
    hardening: HardeningReport,
) -> tuple[int, list[str], str]:
    score = 100
    steps: list[str] = ["Starting score: 100"]

    sev = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0, "INFO": 0}
    for cve in validation.cves_found:
        sev[cve.severity] = sev.get(cve.severity, 0) + 1
        if cve.exploit_available and cve.severity in ("CRITICAL", "HIGH"):
            score -= WEIGHTS["exploit_available_bonus"]
            steps.append(
                f"−{WEIGHTS['exploit_available_bonus']}: exploit available for {cve.cve_id}"
            )

    for s in ("CRITICAL", "HIGH", "MEDIUM", "LOW"):
        if sev[s]:
            deduction = sev[s] * WEIGHTS[f"cve_{s.lower()}"]
            score -= deduction
            steps.append(f"−{deduction}: {sev[s]} {s} CVE(s)")

    if intel.domain_breached:
        score -= WEIGHTS["breach"]
        steps.append(f"−{WEIGHTS['breach']}: domain in {intel.breach_count} breach(es)")

    if len(intel.active_campaigns) >= 3:
        score -= WEIGHTS["active_campaigns_3plus"]
        steps.append(
            f"−{WEIGHTS['active_campaigns_3plus']}: {len(intel.active_campaigns)} active campaigns"
        )

    for ip in intel.suspicious_ips:
        if ip.abuse_confidence >= 75:
            score -= WEIGHTS["abuse_ip_high_confidence"]
            steps.append(
                f"−{WEIGHTS['abuse_ip_high_confidence']}: high-confidence abuse IP {ip.ip}"
            )

    if not intel.domain_breached and len(intel.active_campaigns) < 2:
        score += WEIGHTS["clean_intel_bonus"]
        steps.append(f"+{WEIGHTS['clean_intel_bonus']}: clean intelligence posture")

    credit = len(hardening.actions_taken) * WEIGHTS["hardening_credit_per_action"]
    score += credit
    if credit:
        steps.append(f"+{credit}: hardening credit ({len(hardening.actions_taken)} action(s))")

    score = max(0, min(100, score))
    steps.append(f"Final posture score: {score}/100")
    grade = (
        "A"
        if score >= 90
        else "B"
        if score >= 75
        else "C"
        if score >= 60
        else "D"
        if score >= 40
        else "F"
    )
    return score, steps, grade
