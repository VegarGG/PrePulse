from __future__ import annotations

from backend.agents.base import BaseAgent
from backend.models.schemas import FinalReport, PipelineState
from backend.prompts.investigator import PROMPT
from backend.services.scoring import compute_posture_score

ALLOWED_TOOLS: list[str] = []  # reasoning-only


agent = BaseAgent(
    name="investigator",
    allowed_tools=ALLOWED_TOOLS,
    prompt_template=PROMPT,
    output_schema=FinalReport,
)


async def run(state: PipelineState) -> PipelineState:
    if not (state.intel_report and state.validation_report and state.hardening_report):
        raise RuntimeError(
            "investigator requires intel_report, validation_report, hardening_report"
        )
    score, steps, grade = compute_posture_score(
        state.intel_report, state.validation_report, state.hardening_report
    )
    report = await agent.run_core(
        state.scan_id,
        intel_report_json=state.intel_report.model_dump_json(indent=2),
        validation_report_json=state.validation_report.model_dump_json(indent=2),
        hardening_report_json=state.hardening_report.model_dump_json(indent=2),
        posture_score=score,
        posture_grade=grade,
        score_explanation=" · ".join(steps),
    )
    # Overwrite score / grade / explanation in case the LLM drifted. The
    # deterministic engine is authoritative.
    authoritative = report.model_copy(
        update={
            "posture_score": score,
            "posture_grade": grade,
            "score_explanation": " · ".join(steps),
        }
    )
    return state.model_copy(update={"final_report": authoritative})
