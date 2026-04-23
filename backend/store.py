"""In-memory scan store + dashboard metrics aggregator.

A real deployment would back this with a database. For the prototype the store
lives for the lifetime of the process. Phase 6 can seed synthetic history on
startup (§21) — the aggregator already treats pre-seeded entries identically
to live scans.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any

from backend.models.schemas import CompanyProfile, PipelineState

_scans: dict[str, PipelineState] = {}


def create(state: PipelineState) -> None:
    _scans[state.scan_id] = state


def update(scan_id: str, state: PipelineState) -> None:
    _scans[scan_id] = state


def get(scan_id: str) -> PipelineState | None:
    return _scans.get(scan_id)


def list_all() -> list[PipelineState]:
    return list(_scans.values())


def clear() -> None:
    _scans.clear()


def aggregate_metrics() -> dict[str, Any]:
    scans = [s for s in _scans.values() if s.final_report is not None]
    total_scans = len(scans)
    total_threats = sum(
        len(s.intel_report.active_campaigns) if s.intel_report else 0 for s in scans
    ) + sum(
        len(s.validation_report.cves_found) if s.validation_report else 0 for s in scans
    )
    total_actions = sum(
        (s.remediation_report.actions_executed if s.remediation_report else 0)
        + (len(s.hardening_report.actions_taken) if s.hardening_report else 0)
        for s in scans
    )
    avg_posture = (
        round(sum(s.final_report.posture_score for s in scans) / total_scans, 1)
        if total_scans
        else 0.0
    )

    # posture 30d series — one point per scan
    posture_series = [
        {
            "scan_id": s.scan_id,
            "ts": s.started_at.isoformat(),
            "posture_score": s.final_report.posture_score if s.final_report else None,
            "grade": s.final_report.posture_grade if s.final_report else None,
        }
        for s in scans
    ]

    # severity distribution
    sev_counter: Counter[str] = Counter()
    for s in scans:
        if s.validation_report:
            for cve in s.validation_report.cves_found:
                sev_counter[cve.severity] += 1

    # actions by kind
    action_kinds: Counter[str] = Counter()
    for s in scans:
        if s.remediation_report:
            for a in s.remediation_report.actions:
                if a.executed:
                    action_kinds[a.kind] += 1
        if s.hardening_report:
            for ha in s.hardening_report.actions_taken:
                action_kinds[ha.kind] += 1

    # top tactics
    tactic_counter: dict[str, dict[str, Any]] = defaultdict(
        lambda: {"technique_id": "", "technique_name": "", "tactic": "", "count": 0}
    )
    for s in scans:
        if s.validation_report:
            for t in s.validation_report.mitre_techniques:
                entry = tactic_counter[t.technique_id]
                entry["technique_id"] = t.technique_id
                entry["technique_name"] = t.technique_name
                entry["tactic"] = t.tactic
                entry["count"] += 1
    top_tactics = sorted(
        tactic_counter.values(), key=lambda e: e["count"], reverse=True
    )[:10]

    return {
        "rolling": {
            "total_scans": total_scans,
            "threats_detected": total_threats,
            "actions_executed": total_actions,
            "avg_posture_score": avg_posture,
            "mean_time_to_contain_s": 0,  # Phase 6 when we seed historical data
        },
        "series": {
            "posture_30d": posture_series,
            "severities_30d": dict(sev_counter),
            "actions_30d": dict(action_kinds),
        },
        "top_tactics": top_tactics,
        "agent_stats": [],  # Phase 6 populates this from the trace store
    }


def dashboard_delta(state: PipelineState) -> dict[str, Any]:
    """Return a minimal delta the frontend can apply after scan.completed."""
    return {
        "scan_id": state.scan_id,
        "posture_score": state.final_report.posture_score if state.final_report else None,
        "actions_executed": (
            state.remediation_report.actions_executed if state.remediation_report else 0
        ),
        "threats_detected": (
            len(state.intel_report.active_campaigns) if state.intel_report else 0
        )
        + (len(state.validation_report.cves_found) if state.validation_report else 0),
    }


def _touch_profile(profile: CompanyProfile) -> None:
    """Trivial reference to keep import graph honest; no-op behaviour."""
    _ = profile
