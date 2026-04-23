from __future__ import annotations

from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, Field, field_validator

Severity = Literal["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"]
ActionSeverity = Literal["critical", "high", "medium", "low"]


class CompanyProfile(BaseModel):
    """User-supplied profile that drives the scan."""

    company_name: str = Field(..., max_length=128)
    domain: str = Field(..., description="Primary corporate domain, e.g. rivercity.fin")
    industry: Literal[
        "fintech",
        "healthcare",
        "e-commerce",
        "manufacturing",
        "legal",
        "education",
        "media",
        "saas",
        "other",
    ]
    employee_count: int = Field(..., ge=1, le=5000)
    tech_stack: List[str] = Field(default_factory=list, description="Products/services in use")
    ip_range: Optional[str] = Field(None, description="Optional CIDR to scan")


class ThreatCampaign(BaseModel):
    pulse_id: str
    title: str
    description: str
    threat_level: int = Field(..., ge=1, le=5)
    industry_targeted: str
    tags: List[str] = Field(default_factory=list)
    first_seen: str


class BreachRecord(BaseModel):
    breach_name: str
    date: str
    pwn_count: int
    data_classes: List[str]


class IPReputation(BaseModel):
    ip: str
    abuse_confidence: int = Field(..., ge=0, le=100)
    country: Optional[str] = None
    usage_type: Optional[str] = None
    total_reports: int = 0


class IntelligenceReport(BaseModel):
    domain: str
    active_campaigns: List[ThreatCampaign]
    domain_breached: bool
    breach_count: int = 0
    breaches: List[BreachRecord] = Field(default_factory=list)
    suspicious_ips: List[IPReputation] = Field(default_factory=list)
    raw_summary: str
    confidence: float = Field(..., ge=0.0, le=1.0)


class CVEFinding(BaseModel):
    cve_id: str
    severity: Severity
    cvss_score: Optional[float] = Field(None, ge=0.0, le=10.0)
    description: str
    affected_product: str
    exploit_available: bool = False
    published: str


class MitreTechnique(BaseModel):
    technique_id: str
    technique_name: str
    tactic: str
    description: str
    similarity_score: float = Field(..., ge=0.0, le=1.0)


class ValidationReport(BaseModel):
    cves_found: List[CVEFinding]
    mitre_techniques: List[MitreTechnique]
    exploitable_count: int = 0
    validation_summary: str
    confidence: float = Field(..., ge=0.0, le=1.0)


class HardeningAction(BaseModel):
    action_id: str
    kind: Literal[
        "mtd_port_rotation",
        "mtd_cert_refresh",
        "attack_surface_reduction",
        "identity_posture_tightening",
    ]
    description: str
    target: str
    simulated: bool = True
    executed_at: Optional[datetime] = None
    expected_impact: str


class HardeningReport(BaseModel):
    actions_taken: List[HardeningAction]
    rationale: str
    risk_reduction_estimate: int = Field(
        ...,
        ge=0,
        le=100,
        description="Estimated posture-score improvement from these actions",
    )


class CriticalFinding(BaseModel):
    headline: str
    detail: str
    linked_cves: List[str] = Field(default_factory=list)
    linked_techniques: List[str] = Field(default_factory=list)
    severity: ActionSeverity


class RecommendedAction(BaseModel):
    priority: int = Field(..., ge=1, le=5)
    description: str
    estimated_effort: Literal["<1h", "<1d", "<1w", ">1w"]
    owner_suggestion: Literal["it_admin", "security_engineer", "executive", "vendor"]


class FinalReport(BaseModel):
    posture_score: int = Field(..., ge=0, le=100)
    posture_grade: Literal["A", "B", "C", "D", "F"]
    score_explanation: str
    critical_findings: List[CriticalFinding] = Field(..., min_length=1, max_length=5)
    recommended_actions: List[RecommendedAction] = Field(..., min_length=1, max_length=5)
    executive_summary: str = Field(..., max_length=1200)
    what_prepulse_would_do: str

    @field_validator("posture_grade")
    @classmethod
    def _grade_matches_score(cls, v, info):
        score = info.data.get("posture_score", 0)
        expected = (
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
        if v != expected:
            raise ValueError(f"grade {v} inconsistent with score {score} (expected {expected})")
        return v


class RemediationAction(BaseModel):
    action_id: str
    kind: Literal[
        "firewall.block_ip",
        "firewall.block_range",
        "iam.force_mfa",
        "iam.rotate_credentials",
        "iam.disable_user",
        "endpoint.isolate",
        "endpoint.quarantine_file",
        "ticketing.open_incident",
        "email.notify_admin",
    ]
    severity: ActionSeverity
    args: dict
    requires_approval: bool = True
    approved: Optional[bool] = None
    executed: bool = False
    executed_at: Optional[datetime] = None
    result_summary: Optional[str] = None


class RemediationReport(BaseModel):
    actions: List[RemediationAction]
    actions_approved: int
    actions_executed: int
    actions_rejected: int
    incident_ticket_id: Optional[str] = None


class ConfidenceFlag(BaseModel):
    agent: str
    reason: str
    severity: Literal["warning", "error"]
    suggested_human_review: bool = True


class SupervisorReport(BaseModel):
    overall_confidence: float = Field(..., ge=0.0, le=1.0)
    flags: List[ConfidenceFlag] = Field(default_factory=list)
    policy_violations: List[str] = Field(default_factory=list)
    escalated_to_human: bool = False
    audit_trail_id: str
    sign_off: Literal["approved", "conditional", "escalate"]


class PipelineState(BaseModel):
    scan_id: str
    started_at: datetime
    profile: CompanyProfile
    intel_report: Optional[IntelligenceReport] = None
    validation_report: Optional[ValidationReport] = None
    hardening_report: Optional[HardeningReport] = None
    final_report: Optional[FinalReport] = None
    remediation_report: Optional[RemediationReport] = None
    supervisor_report: Optional[SupervisorReport] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
