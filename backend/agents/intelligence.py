from __future__ import annotations

from backend.agents.base import BaseAgent
from backend.models.schemas import IntelligenceReport, PipelineState
from backend.prompts.intelligence import PROMPT

ALLOWED_TOOLS = ["otx.get_pulses", "hibp.check_domain", "abuseipdb.check_ip"]


def _sample_ip(profile) -> str:
    if profile.ip_range and "/" in profile.ip_range:
        base = profile.ip_range.split("/")[0]
        octets = base.split(".")
        if len(octets) == 4:
            octets[-1] = "23"
            return ".".join(octets)
    return "8.8.8.8"


agent = BaseAgent(
    name="intelligence",
    allowed_tools=ALLOWED_TOOLS,
    prompt_template=PROMPT,
    output_schema=IntelligenceReport,
)


async def run(state: PipelineState, sample_ip: str | None = None) -> PipelineState:
    p = state.profile
    report = await agent.run_core(
        state.scan_id,
        company_name=p.company_name,
        domain=p.domain,
        industry=p.industry,
        employee_count=p.employee_count,
        tech_stack=", ".join(p.tech_stack) or "(none declared)",
        ip_range=p.ip_range or "(none declared)",
        sample_ip=sample_ip or _sample_ip(p),
    )
    return state.model_copy(update={"intel_report": report})
