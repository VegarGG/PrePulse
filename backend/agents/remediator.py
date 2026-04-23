from __future__ import annotations

import os
from datetime import datetime

from backend.agents.base import BaseAgent
from backend.events import emit
from backend.models.schemas import PipelineState, RemediationReport
from backend.prompts.remediator import PROMPT
from backend.services.approvals import await_approval, register_pending, resolve_approval
from backend.tools.base import TOOLS

# The LLM turn plans only. Execution happens in _execute_plan() after the
# human-in-the-loop gate (or auto-approve in test mode).
ALLOWED_TOOLS: list[str] = []

APPROVAL_TIMEOUT_S = float(os.getenv("PREPULSE_APPROVAL_TIMEOUT", "120"))


agent = BaseAgent(
    name="remediator",
    allowed_tools=ALLOWED_TOOLS,
    prompt_template=PROMPT,
    output_schema=RemediationReport,
)


async def _execute_plan(scan_id: str, report: RemediationReport) -> RemediationReport:
    auto_approve = os.getenv("PREPULSE_AUTO_APPROVE") == "1"
    ticket_id: str | None = None

    for action in report.actions:
        gated = action.severity in ("critical", "high") or action.requires_approval
        approved: bool

        if gated and not auto_approve:
            register_pending(scan_id, action.action_id)
            await emit(
                scan_id,
                "action.pending",
                {
                    "action_id": action.action_id,
                    "action": action.kind,
                    "severity": action.severity,
                    "args": action.args,
                },
            )
            approved = await await_approval(scan_id, action.action_id, timeout=APPROVAL_TIMEOUT_S)
            await emit(
                scan_id,
                "action.approved" if approved else "action.rejected",
                {"action_id": action.action_id},
            )
        else:
            # auto-execute low/medium, or in auto-approve mode
            if gated and auto_approve:
                # still emit the pending → approved pair so the UI sees the gate
                await emit(
                    scan_id,
                    "action.pending",
                    {
                        "action_id": action.action_id,
                        "action": action.kind,
                        "severity": action.severity,
                        "args": action.args,
                    },
                )
                await emit(scan_id, "action.approved", {"action_id": action.action_id, "auto": True})
            approved = True

        action.approved = approved
        if not approved:
            continue

        tool_fn = TOOLS.get(action.kind)
        if tool_fn is None:
            action.executed = False
            action.result_summary = f"unknown tool: {action.kind}"
            continue

        try:
            result = await tool_fn(scan_id, **action.args)
        except Exception as e:  # keep the scan moving even if one simulated tool trips
            action.executed = False
            action.result_summary = f"error: {type(e).__name__}: {e}"
            continue

        action.executed = True
        action.executed_at = datetime.utcnow()
        action.result_summary = str(result.get("message", "executed"))
        if action.kind == "ticketing.open_incident" and ticket_id is None:
            ticket_id = str(result.get("ticket_id") or "")
        await emit(
            scan_id,
            "action.executed",
            {"action_id": action.action_id, "result": result},
        )

    report.actions_approved = sum(1 for a in report.actions if a.approved)
    report.actions_executed = sum(1 for a in report.actions if a.executed)
    report.actions_rejected = sum(1 for a in report.actions if a.approved is False)
    report.incident_ticket_id = ticket_id
    return report


async def run(state: PipelineState) -> PipelineState:
    if state.final_report is None:
        raise RuntimeError("remediator requires final_report")
    hardening_json = (
        state.hardening_report.model_dump_json(indent=2)
        if state.hardening_report
        else "[]"
    )
    report: RemediationReport = await agent.run_core(  # type: ignore[assignment]
        state.scan_id,
        final_report_json=state.final_report.model_dump_json(indent=2),
        hardening_actions_json=hardening_json,
    )
    report = await _execute_plan(state.scan_id, report)
    return state.model_copy(update={"remediation_report": report})


__all__ = ["run", "agent", "resolve_approval"]
