from __future__ import annotations

from backend.agents.base import BaseAgent
from backend.models.schemas import IntelligenceReport, PipelineState, ValidationReport
from backend.prompts.validator import PROMPT

ALLOWED_TOOLS = ["nvd.query_cves", "mitre.match_techniques"]


def _summarize_intel(report: IntelligenceReport) -> str:
    lines: list[str] = [f"Domain breached: {report.domain_breached} (breach count: {report.breach_count})"]
    for c in report.active_campaigns[:5]:
        lines.append(f"- Campaign: {c.title} [lvl={c.threat_level}] tags={c.tags}")
    for ip in report.suspicious_ips[:3]:
        lines.append(f"- Suspicious IP: {ip.ip} abuse_confidence={ip.abuse_confidence}")
    return "\n".join(lines)


agent = BaseAgent(
    name="validator",
    allowed_tools=ALLOWED_TOOLS,
    prompt_template=PROMPT,
    output_schema=ValidationReport,
)


async def run(state: PipelineState) -> PipelineState:
    if state.intel_report is None:
        raise RuntimeError("validator requires state.intel_report")
    p = state.profile
    report = await agent.run_core(
        state.scan_id,
        industry=p.industry,
        tech_stack=", ".join(p.tech_stack) or "(none declared)",
        intel_summary=_summarize_intel(state.intel_report),
    )
    return state.model_copy(update={"validation_report": report})
