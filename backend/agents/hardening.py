from __future__ import annotations

from backend.agents.base import BaseAgent
from backend.models.schemas import (
    HardeningReport,
    IntelligenceReport,
    PipelineState,
    ValidationReport,
)
from backend.prompts.hardening import PROMPT

ALLOWED_TOOLS = ["mtd.rotate_port_map", "mtd.refresh_certs", "iam.rotate_credentials"]


def _summarize_intel(r: IntelligenceReport) -> str:
    return (
        f"{len(r.active_campaigns)} active campaigns; breached={r.domain_breached}; "
        f"top_campaign={(r.active_campaigns[0].title if r.active_campaigns else 'none')}"
    )


def _summarize_validation(r: ValidationReport) -> str:
    severities = [c.severity for c in r.cves_found]
    return (
        f"{len(r.cves_found)} CVEs ({severities}); exploitable={r.exploitable_count}; "
        f"techniques={[t.technique_id for t in r.mitre_techniques[:3]]}"
    )


agent = BaseAgent(
    name="hardening",
    allowed_tools=ALLOWED_TOOLS,
    prompt_template=PROMPT,
    output_schema=HardeningReport,
)


async def run(state: PipelineState) -> PipelineState:
    if state.intel_report is None:
        raise RuntimeError("hardening requires intel_report")
    # validation_report may still be None — hardening runs in parallel with
    # the validator node, so we only use it opportunistically.
    validation_summary = (
        _summarize_validation(state.validation_report)
        if state.validation_report
        else "(validator not yet available — operate on intel signal alone)"
    )
    report = await agent.run_core(
        state.scan_id,
        intel_summary=_summarize_intel(state.intel_report),
        validation_summary=validation_summary,
    )
    return state.model_copy(update={"hardening_report": report})
