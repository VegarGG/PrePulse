from __future__ import annotations

from backend.agents.base import BaseAgent
from backend.events import emit
from backend.models.schemas import PipelineState, SupervisorReport
from backend.prompts.supervisor import PROMPT

ALLOWED_TOOLS = ["policy.check", "audit.log_decision"]


agent = BaseAgent(
    name="supervisor",
    allowed_tools=ALLOWED_TOOLS,
    prompt_template=PROMPT,
    output_schema=SupervisorReport,
)


async def run(state: PipelineState) -> PipelineState:
    prior = {
        "intel": state.intel_report.model_dump() if state.intel_report else None,
        "validation": state.validation_report.model_dump() if state.validation_report else None,
        "hardening": state.hardening_report.model_dump() if state.hardening_report else None,
        "final": state.final_report.model_dump() if state.final_report else None,
    }
    remediation_actions: list[dict] = []
    if state.remediation_report:
        remediation_actions = [a.model_dump() for a in state.remediation_report.actions]

    import json as _json

    report: SupervisorReport = await agent.run_core(  # type: ignore[assignment]
        state.scan_id,
        all_reports_json=_json.dumps(prior, default=str, indent=2),
        remediation_actions_json=_json.dumps(remediation_actions, default=str, indent=2),
    )
    for flag in report.flags:
        await emit(
            state.scan_id,
            "confidence.flagged",
            {"agent": flag.agent, "reason": flag.reason, "severity": flag.severity},
        )
    return state.model_copy(update={"supervisor_report": report})
