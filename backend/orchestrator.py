"""LangGraph pipeline + run_scan() entry point.

Topology (§11):
    intelligence ──► validator ──┐
                 └► hardening ──┼► investigator ─┬─ score < 75 ─► remediator ─► supervisor ─► END
                                                 └─ score ≥ 75 ──────────────► supervisor ─► END
"""

from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Any

from langgraph.graph import END, StateGraph

from backend import store
from backend.agents import (
    hardening as hardening_agent,
    intelligence as intelligence_agent,
    investigator as investigator_agent,
    remediator as remediator_agent,
    supervisor as supervisor_agent,
    validator as validator_agent,
)
from backend.events import emit
from backend.models.schemas import CompanyProfile, PipelineState


async def _run_intelligence(state: PipelineState) -> dict[str, Any]:
    new_state = await intelligence_agent.run(state)
    return {"intel_report": new_state.intel_report}


async def _run_validator(state: PipelineState) -> dict[str, Any]:
    new_state = await validator_agent.run(state)
    return {"validation_report": new_state.validation_report}


async def _run_hardening(state: PipelineState) -> dict[str, Any]:
    new_state = await hardening_agent.run(state)
    return {"hardening_report": new_state.hardening_report}


async def _run_investigator(state: PipelineState) -> dict[str, Any]:
    new_state = await investigator_agent.run(state)
    return {"final_report": new_state.final_report}


async def _run_remediator(state: PipelineState) -> dict[str, Any]:
    new_state = await remediator_agent.run(state)
    return {"remediation_report": new_state.remediation_report}


async def _run_supervisor(state: PipelineState) -> dict[str, Any]:
    new_state = await supervisor_agent.run(state)
    return {"supervisor_report": new_state.supervisor_report}


def _route_after_investigator(state: PipelineState) -> str:
    if state.final_report is None:
        return "supervisor"
    return "remediator" if state.final_report.posture_score < 75 else "supervisor"


def build_graph():
    g = StateGraph(PipelineState)
    g.add_node("intelligence", _run_intelligence)
    g.add_node("validator", _run_validator)
    g.add_node("hardening", _run_hardening)
    g.add_node("investigator", _run_investigator)
    g.add_node("remediator", _run_remediator)
    g.add_node("supervisor", _run_supervisor)

    g.set_entry_point("intelligence")

    g.add_edge("intelligence", "validator")
    g.add_edge("intelligence", "hardening")

    g.add_edge("validator", "investigator")
    g.add_edge("hardening", "investigator")

    g.add_conditional_edges(
        "investigator",
        _route_after_investigator,
        {"remediator": "remediator", "supervisor": "supervisor"},
    )
    g.add_edge("remediator", "supervisor")
    g.add_edge("supervisor", END)

    return g.compile()


_GRAPH = None


def get_graph():
    global _GRAPH
    if _GRAPH is None:
        _GRAPH = build_graph()
    return _GRAPH


async def _run_scan_async(scan_id: str, profile: CompanyProfile) -> None:
    state = PipelineState(scan_id=scan_id, started_at=datetime.utcnow(), profile=profile)
    store.create(state)
    await emit(scan_id, "scan.started", {"profile": profile.model_dump()})
    try:
        graph = get_graph()
        raw = await graph.ainvoke(state)
        final_state = raw if isinstance(raw, PipelineState) else PipelineState.model_validate(raw)
        final_state = final_state.model_copy(update={"completed_at": datetime.utcnow()})
        store.update(scan_id, final_state)
        await emit(
            scan_id,
            "scan.completed",
            {
                "final_report": final_state.final_report.model_dump() if final_state.final_report else None,
                "dashboard_delta": store.dashboard_delta(final_state),
            },
        )
    except Exception as e:
        store.update(
            scan_id,
            state.model_copy(update={"error": f"{type(e).__name__}: {e}"}),
        )
        await emit(scan_id, "scan.failed", {"error": str(e), "stage": "pipeline"})
        raise


def run_scan(scan_id: str, profile: CompanyProfile) -> asyncio.Task:
    """Launch the scan as a background task and return immediately."""
    return asyncio.create_task(_run_scan_async(scan_id, profile))
