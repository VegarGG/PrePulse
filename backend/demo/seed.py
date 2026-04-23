"""Historical-scan seed generator.

Builds a deterministic 30-day stream of synthetic scans and inserts them into
the in-memory store on backend startup (§21). The dashboard is never empty
during a showcase demo; the KPI strip, posture trend, severity distribution,
actions-by-kind, and top tactics all render from the seed immediately.

All data is synthetic. Random seed is fixed so the dashboard looks identical
on every boot.
"""

from __future__ import annotations

import random
from datetime import datetime, timedelta

from backend import store
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

COMPANIES = [
    (
        "river_city",
        "River City Financial Services",
        "rivercity.fin",
        "fintech",
        87,
        ["AWS Lambda", "PostgreSQL", "Stripe", "GitHub Enterprise", "Slack"],
        "198.51.100.0/24",
    ),
    (
        "greenfield",
        "Greenfield Family Clinic",
        "greenfieldclinic.health",
        "healthcare",
        42,
        ["Microsoft Exchange 2019", "Windows Server 2019", "Veeam Backup", "Outlook"],
        "203.0.113.0/24",
    ),
    (
        "shoplocal",
        "ShopLocal Marketplace",
        "shoplocal.market",
        "e-commerce",
        120,
        ["Shopify", "Cloudflare", "MySQL", "Stripe"],
        "192.0.2.0/24",
    ),
    (
        "northstar",
        "Northstar Logistics",
        "northstar-logistics.test",
        "manufacturing",
        180,
        ["SAP", "Oracle DB", "Windows Server 2022"],
        None,
    ),
    (
        "eastbay",
        "Eastbay Legal Group",
        "eastbay-law.test",
        "legal",
        35,
        ["Microsoft 365", "Clio", "DocuSign"],
        None,
    ),
]

CAMPAIGN_TITLES = [
    "Grandoreiro Banking Trojan — North America Campaign",
    "Magecart Cardskimmer v7 — Payment Page Injection",
    "BlackBasta Ransomware — Healthcare Wave",
    "ProxyNotShell Variant — Unpatched Exchange",
    "OAuth Token Harvesting via Third-Party Slack Apps",
    "Lazarus npm Supply-Chain Compromise",
    "PHI Exfiltration via Misconfigured FHIR Endpoints",
    "Stripe SDK Signature Bypass PoC",
]

CAMPAIGN_TAGS = [
    "banking-trojan",
    "ransomware",
    "spearphishing",
    "cardskimmer",
    "exchange",
    "healthcare",
    "supply-chain",
    "oauth",
    "rce",
    "credential-theft",
]

TECHNIQUE_POOL = [
    ("T1190", "Exploit Public-Facing Application", "Initial Access"),
    ("T1566.001", "Spearphishing Attachment", "Initial Access"),
    ("T1566.002", "Spearphishing Link", "Initial Access"),
    ("T1078", "Valid Accounts", "Initial Access"),
    ("T1059.001", "PowerShell", "Execution"),
    ("T1053.005", "Scheduled Task", "Persistence"),
    ("T1003.001", "LSASS Memory", "Credential Access"),
    ("T1110.003", "Password Spraying", "Credential Access"),
    ("T1555", "Credentials from Password Stores", "Credential Access"),
    ("T1021.001", "Remote Desktop Protocol", "Lateral Movement"),
    ("T1486", "Data Encrypted for Impact", "Impact"),
    ("T1041", "Exfiltration Over C2 Channel", "Exfiltration"),
    ("T1567.002", "Exfiltration to Cloud Storage", "Exfiltration"),
]

REMEDIATION_KINDS = [
    "firewall.block_ip",
    "firewall.block_range",
    "iam.force_mfa",
    "iam.rotate_credentials",
    "endpoint.isolate",
    "ticketing.open_incident",
    "email.notify_admin",
]

HARDENING_KINDS = [
    "mtd_port_rotation",
    "mtd_cert_refresh",
    "attack_surface_reduction",
    "identity_posture_tightening",
]


def _build_state(
    rnd: random.Random, scan_id: str, ts: datetime, company: tuple, posture: int
) -> PipelineState:
    profile = CompanyProfile(
        company_name=company[1],
        domain=company[2],
        industry=company[3],
        employee_count=company[4],
        tech_stack=list(company[5]),
        ip_range=company[6],
    )

    # Intelligence
    n_campaigns = rnd.choices([0, 1, 2, 3, 4], weights=[1, 3, 4, 3, 1], k=1)[0]
    campaigns = [
        ThreatCampaign(
            pulse_id=f"otx-hist-{ts.strftime('%Y%m%d')}-{scan_id}-{i}",
            title=rnd.choice(CAMPAIGN_TITLES),
            description="Historical synthetic campaign for dashboard seeding.",
            threat_level=rnd.choices([2, 3, 4, 5], weights=[2, 3, 3, 2], k=1)[0],
            industry_targeted=profile.industry,
            tags=rnd.sample(CAMPAIGN_TAGS, k=min(3, len(CAMPAIGN_TAGS))),
            first_seen=(ts - timedelta(days=rnd.randint(1, 30))).isoformat(),
        )
        for i in range(n_campaigns)
    ]
    breached = rnd.random() < 0.35
    intel = IntelligenceReport(
        domain=profile.domain,
        active_campaigns=campaigns,
        domain_breached=breached,
        breach_count=rnd.randint(1, 2) if breached else 0,
        breaches=(
            [
                BreachRecord(
                    breach_name="Historical Credential Dump",
                    date="2022-06-15",
                    pwn_count=rnd.randint(5_000_000, 800_000_000),
                    data_classes=["Email addresses", "Passwords"],
                )
            ]
            if breached
            else []
        ),
        suspicious_ips=[
            IPReputation(
                ip=f"198.51.100.{rnd.randint(1, 254)}",
                abuse_confidence=rnd.randint(10, 95),
                country=rnd.choice(["US", "RU", "CN", "BR"]),
                usage_type="Data Center/Web Hosting/Transit",
                total_reports=rnd.randint(0, 150),
            )
        ],
        raw_summary="Synthetic historical summary.",
        confidence=round(rnd.uniform(0.7, 0.95), 2),
    )

    # Validation
    n_cves = rnd.choices([1, 2, 3, 4, 5], weights=[1, 2, 3, 2, 1], k=1)[0]
    sev_pool = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
    sev_weights = [1, 2, 3, 2]
    cves = [
        CVEFinding(
            cve_id=f"CVE-{rnd.choice([2023, 2024, 2025, 2026])}-{rnd.randint(10000, 99999)}",
            severity=rnd.choices(sev_pool, weights=sev_weights, k=1)[0],  # type: ignore[arg-type]
            cvss_score=round(rnd.uniform(3.0, 9.9), 1),
            description="Historical synthetic vulnerability.",
            affected_product=rnd.choice(profile.tech_stack or ["Generic Service"]),
            exploit_available=rnd.random() < 0.3,
            published=(ts - timedelta(days=rnd.randint(30, 540))).strftime("%Y-%m-%d"),
        )
        for _ in range(n_cves)
    ]
    n_techs = rnd.randint(2, 4)
    # Weight towards Initial Access / Credential Access / Exfiltration per §21
    weights_by_tactic = {
        "Initial Access": 4,
        "Credential Access": 3,
        "Exfiltration": 3,
        "Execution": 2,
        "Persistence": 2,
        "Lateral Movement": 2,
        "Impact": 2,
    }
    pool_weighted = [
        (tid, tname, tactic, weights_by_tactic.get(tactic, 1))
        for tid, tname, tactic in TECHNIQUE_POOL
    ]
    picks = rnd.choices(pool_weighted, weights=[w for *_, w in pool_weighted], k=n_techs)
    techs = [
        MitreTechnique(
            technique_id=tid,
            technique_name=tname,
            tactic=tactic,
            description="Historical synthetic technique match.",
            similarity_score=round(rnd.uniform(0.6, 0.95), 2),
        )
        for tid, tname, tactic, _ in picks
    ]
    validation = ValidationReport(
        cves_found=cves,
        mitre_techniques=techs,
        exploitable_count=sum(1 for c in cves if c.exploit_available),
        validation_summary="Historical synthetic summary.",
        confidence=round(rnd.uniform(0.7, 0.95), 2),
    )

    # Hardening
    n_hard = rnd.randint(1, 3)
    hardening = HardeningReport(
        actions_taken=[
            HardeningAction(
                action_id=f"h-{scan_id}-{i}",
                kind=rnd.choice(HARDENING_KINDS),  # type: ignore[arg-type]
                description="Historical synthetic hardening action.",
                target="edge-gateway",
                executed_at=ts,
                expected_impact="Recon invalidation",
            )
            for i in range(n_hard)
        ],
        rationale="Historical synthetic rationale.",
        risk_reduction_estimate=rnd.randint(2, 10),
    )

    # Final
    grade = (
        "A"
        if posture >= 90
        else "B"
        if posture >= 75
        else "C"
        if posture >= 60
        else "D"
        if posture >= 40
        else "F"
    )
    final = FinalReport(
        posture_score=posture,
        posture_grade=grade,  # type: ignore[arg-type]
        score_explanation="Historical synthetic score breakdown.",
        critical_findings=[
            CriticalFinding(
                headline=f"Exposure on {profile.tech_stack[0] if profile.tech_stack else 'service'}",
                detail="Historical synthetic finding.",
                linked_cves=[cves[0].cve_id] if cves else [],
                linked_techniques=[techs[0].technique_id] if techs else [],
                severity=rnd.choice(["high", "medium", "low"]),  # type: ignore[arg-type]
            )
        ],
        recommended_actions=[
            RecommendedAction(
                priority=1,
                description="Historical synthetic recommendation.",
                estimated_effort=rnd.choice(["<1h", "<1d", "<1w"]),  # type: ignore[arg-type]
                owner_suggestion=rnd.choice(["it_admin", "security_engineer"]),  # type: ignore[arg-type]
            )
        ],
        executive_summary=f"Historical synthetic scan for {profile.company_name}.",
        what_prepulse_would_do="Historical synthetic response narrative.",
    )

    # Remediation — only low-posture runs trigger it, matching the §11 conditional route
    rem: RemediationReport | None = None
    if posture < 75:
        n_rem = rnd.randint(1, 4)
        rem_actions = [
            RemediationAction(
                action_id=f"r-{scan_id}-{i}",
                kind=rnd.choice(REMEDIATION_KINDS),  # type: ignore[arg-type]
                severity=rnd.choice(["low", "medium", "high", "critical"]),  # type: ignore[arg-type]
                args={},
                requires_approval=True,
                approved=True,
                executed=True,
                executed_at=ts + timedelta(seconds=rnd.randint(5, 40)),
                result_summary="Historical synthetic execution.",
            )
            for i in range(n_rem)
        ]
        rem = RemediationReport(
            actions=rem_actions,
            actions_approved=n_rem,
            actions_executed=n_rem,
            actions_rejected=0,
            incident_ticket_id=f"inc-HIST{rnd.randint(1000, 9999)}",
        )

    sup = SupervisorReport(
        overall_confidence=round(rnd.uniform(0.75, 0.95), 2),
        flags=[],
        policy_violations=[],
        escalated_to_human=posture < 40,
        audit_trail_id=f"audit-hist{rnd.randint(10000, 99999)}",
        sign_off="approved" if posture >= 60 else ("conditional" if posture >= 40 else "escalate"),  # type: ignore[arg-type]
    )

    return PipelineState(
        scan_id=scan_id,
        started_at=ts,
        profile=profile,
        intel_report=intel,
        validation_report=validation,
        hardening_report=hardening,
        final_report=final,
        remediation_report=rem,
        supervisor_report=sup,
        completed_at=ts + timedelta(seconds=rnd.randint(30, 90)),
    )


def seed_history(
    *,
    now: datetime | None = None,
    days: int = 30,
    per_day: int = 4,
    seed: int = 42,
) -> int:
    """Insert ~days×per_day synthetic scans into the store. Idempotent-ish:
    callers that want a clean slate should call store.clear() first.
    """
    rnd = random.Random(seed)
    now = now or datetime.utcnow()
    dip_days = {7, 14, 21}  # three narrative dips over the 30-day window
    count = 0
    for d in range(days):
        day_offset = days - d - 1
        day_ts = now - timedelta(days=day_offset)
        n_scans = per_day + rnd.choice([-1, 0, 0, 0, 1])
        base_posture = 72 if d not in dip_days else 38
        for i in range(n_scans):
            hour = rnd.randint(8, 18)
            minute = rnd.randint(0, 59)
            second = rnd.randint(0, 59)
            ts = day_ts.replace(hour=hour, minute=minute, second=second, microsecond=0)
            company = rnd.choice(COMPANIES)
            jitter = rnd.randint(-10, 12)
            posture = max(0, min(100, base_posture + jitter))
            scan_id = f"hist-{ts.strftime('%m%d-%H%M%S')}-{i}"
            state = _build_state(rnd, scan_id, ts, company, posture)
            store.create(state)
            store.update(scan_id, state)
            count += 1
    return count
