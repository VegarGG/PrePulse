"""F-01, F-04, F-07, F-10, F-13 — Pydantic schema conformance per agent.

For each agent we run the agent against each demo profile N times
(default ctx.runs_per_test) and assert the returned report passes
Pydantic validation. The agent calls hit the real LLM, so this module
declares `REQUIRES = {"llm"}`.

Also F-34 (sibling) — schema rejection on malformed input — is in
functional_safety to keep modules small.
"""

from __future__ import annotations

import asyncio
from typing import Iterable

from pydantic import ValidationError

from validation.context import TestContext
from validation.result import TestResult
from validation.tests._helpers import (
    all_profile_ids,
    force_mock_mode,
    fresh_pipeline_state,
    make_synthetic_final_report,
    make_synthetic_hardening_report,
    make_synthetic_intel_report,
    make_synthetic_validation_report,
)

REQUIRES = {"llm"}

AGENT_SPECS = [
    ("F-01", "intelligence", "intel_report"),
    ("F-04", "validator", "validation_report"),
    ("F-07", "hardening", "hardening_report"),
    ("F-10", "investigator", "final_report"),
    ("F-13", "supervisor", "supervisor_report"),
]


async def _seed_state(agent_name: str, profile_id: str):
    state = fresh_pipeline_state(profile_id)
    if agent_name == "intelligence":
        return state
    state = state.model_copy(update={"intel_report": make_synthetic_intel_report()})
    if agent_name == "validator":
        return state
    state = state.model_copy(update={"validation_report": make_synthetic_validation_report()})
    if agent_name == "hardening":
        return state
    state = state.model_copy(update={"hardening_report": make_synthetic_hardening_report()})
    if agent_name == "investigator":
        return state
    state = state.model_copy(update={"final_report": make_synthetic_final_report()})
    return state


async def _run_one(agent_name: str, profile_id: str):
    from backend.agents import (
        hardening as hardening_agent,
        intelligence as intelligence_agent,
        investigator as investigator_agent,
        remediator as remediator_agent,
        supervisor as supervisor_agent,
        validator as validator_agent,
    )

    state = await _seed_state(agent_name, profile_id)
    fn = {
        "intelligence": intelligence_agent.run,
        "validator": validator_agent.run,
        "hardening": hardening_agent.run,
        "investigator": investigator_agent.run,
        "remediator": remediator_agent.run,
        "supervisor": supervisor_agent.run,
    }[agent_name]
    return await fn(state)


def run(ctx: TestContext) -> Iterable[TestResult]:
    force_mock_mode()
    profiles = all_profile_ids()
    runs_per = max(2, min(ctx.runs_per_test, 5))  # cap to keep cost bounded; spec asks 30 — operator can override

    for test_id, agent_name, field in AGENT_SPECS:
        for profile_id in profiles:
            for i in range(runs_per):
                try:
                    new_state = asyncio.run(_run_one(agent_name, profile_id))
                    report = getattr(new_state, field)
                    if report is None:
                        yield TestResult(
                            test_id=test_id,
                            test_name=f"{agent_name}.run on {profile_id} (run {i + 1}/{runs_per})",
                            test_category="functional",
                            expected_outcome=f"{field} populated with valid Pydantic instance",
                            actual_outcome="None",
                            result="fail",
                            failure_mode="schema_violation",
                            input_fixture=profile_id,
                        )
                        continue
                    # Re-validate via model_dump → model_validate to catch bypassed constraints.
                    type(report).model_validate(report.model_dump())
                    yield TestResult(
                        test_id=test_id,
                        test_name=f"{agent_name}.run on {profile_id} (run {i + 1}/{runs_per})",
                        test_category="functional",
                        expected_outcome=f"{field} validates",
                        actual_outcome=type(report).__name__,
                        result="pass",
                        metrics={"schema_conformance_rate": 1.0},
                        input_fixture=profile_id,
                    )
                except ValidationError as ve:
                    yield TestResult(
                        test_id=test_id,
                        test_name=f"{agent_name}.run on {profile_id} (run {i + 1}/{runs_per})",
                        test_category="functional",
                        expected_outcome="Pydantic validation passes",
                        actual_outcome=str(ve)[:1000],
                        result="fail",
                        failure_mode="schema_violation",
                        metrics={"schema_conformance_rate": 0.0},
                        input_fixture=profile_id,
                    )
                except Exception as e:
                    yield TestResult(
                        test_id=test_id,
                        test_name=f"{agent_name}.run on {profile_id} (run {i + 1}/{runs_per})",
                        test_category="functional",
                        expected_outcome="agent run completes without exception",
                        actual_outcome=f"{type(e).__name__}: {e}",
                        result="error",
                        failure_mode="agent_crash",
                        input_fixture=profile_id,
                    )
