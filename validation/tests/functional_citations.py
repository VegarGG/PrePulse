"""F-02 — Intelligence/Validator/Investigator CVE citations exist in NVD.
F-05 — Validator MITRE technique IDs exist in ATT&CK STIX.
F-08 — Hardening proposes only tools that exist in the registry.

Ground truth in mock mode: the demo NVD/MITRE fixtures are the
authoritative known-good set. Any CVE/technique an agent emits that is
not in the union of those fixtures (across all three demo profiles) is
flagged as hallucinated.
"""

from __future__ import annotations

import asyncio
from typing import Iterable

from validation.context import TestContext
from validation.result import TestResult
from validation.tests._helpers import (
    all_profile_ids,
    extract_cve_ids,
    extract_mitre_ids,
    force_mock_mode,
    fresh_pipeline_state,
    known_cve_ids_from_fixtures,
    known_mitre_ids_from_fixtures,
    make_synthetic_intel_report,
    make_synthetic_validation_report,
)

REQUIRES = {"llm"}


async def _run_intel(profile_id: str):
    from backend.agents import intelligence

    return await intelligence.run(fresh_pipeline_state(profile_id))


async def _run_validator(profile_id: str):
    from backend.agents import validator

    state = fresh_pipeline_state(profile_id).model_copy(
        update={"intel_report": make_synthetic_intel_report()}
    )
    return await validator.run(state)


async def _run_investigator(profile_id: str):
    from backend.agents import investigator

    state = fresh_pipeline_state(profile_id).model_copy(
        update={
            "intel_report": make_synthetic_intel_report(),
            "validation_report": make_synthetic_validation_report(),
            "hardening_report": _hardening(),
        }
    )
    return await investigator.run(state)


def _hardening():
    from validation.tests._helpers import make_synthetic_hardening_report

    return make_synthetic_hardening_report()


async def _run_hardening(profile_id: str):
    from backend.agents import hardening

    state = fresh_pipeline_state(profile_id).model_copy(
        update={
            "intel_report": make_synthetic_intel_report(),
            "validation_report": make_synthetic_validation_report(),
        }
    )
    return await hardening.run(state)


def run(ctx: TestContext) -> Iterable[TestResult]:
    force_mock_mode()
    known_cves = known_cve_ids_from_fixtures()
    known_mitre = known_mitre_ids_from_fixtures()

    from backend.tools.base import TOOLS

    registered_tools = set(TOOLS.keys())

    for profile_id in all_profile_ids():
        # F-02 — Intelligence cited CVEs
        try:
            state = asyncio.run(_run_intel(profile_id))
            intel = state.intel_report
            cited = extract_cve_ids(intel.raw_summary or "", *(c.description for c in intel.active_campaigns))
            hallucinated = cited - known_cves
            yield TestResult(
                test_id="F-02",
                test_name=f"Intelligence CVE citations vs NVD fixture ({profile_id})",
                test_category="functional",
                expected_outcome="zero hallucinated CVE ids",
                actual_outcome=(
                    f"cited={sorted(cited)}, hallucinated={sorted(hallucinated)}"
                ),
                result="pass" if not hallucinated else "fail",
                failure_mode=None if not hallucinated else "hallucination",
                metrics={"hallucinated_identifier_rate": len(hallucinated) / max(1, len(cited))},
                input_fixture=profile_id,
            )
        except Exception as e:
            yield TestResult(
                test_id="F-02",
                test_name=f"Intelligence CVE citations ({profile_id})",
                test_category="functional",
                expected_outcome="agent run + extract CVEs",
                actual_outcome=f"{type(e).__name__}: {e}",
                result="error",
                failure_mode="agent_crash",
                input_fixture=profile_id,
            )

        # F-05 — Validator cited MITRE techniques
        try:
            state = asyncio.run(_run_validator(profile_id))
            techs = state.validation_report.mitre_techniques
            cited = {t.technique_id.upper() for t in techs}
            hallucinated = cited - known_mitre
            yield TestResult(
                test_id="F-05",
                test_name=f"Validator MITRE technique ids ({profile_id})",
                test_category="functional",
                expected_outcome="zero hallucinated technique ids",
                actual_outcome=f"cited={sorted(cited)}, hallucinated={sorted(hallucinated)}",
                result="pass" if not hallucinated else "fail",
                failure_mode=None if not hallucinated else "hallucination",
                metrics={"hallucinated_identifier_rate": len(hallucinated) / max(1, len(cited))},
                input_fixture=profile_id,
            )
        except Exception as e:
            yield TestResult(
                test_id="F-05",
                test_name=f"Validator MITRE technique ids ({profile_id})",
                test_category="functional",
                expected_outcome="agent run + extract techniques",
                actual_outcome=f"{type(e).__name__}: {e}",
                result="error",
                failure_mode="agent_crash",
                input_fixture=profile_id,
            )

        # F-08 — Hardening proposes only tools that exist in the registry.
        # The hardening agent's actions reference logical kinds (mtd_port_rotation,
        # mtd_cert_refresh, ...). The plan asks that any tool the agent invokes
        # exists in TOOLS. We approximate by checking the tool.called events
        # logged during the run against the registry.
        try:
            from backend.events import get_history

            state = asyncio.run(_run_hardening(profile_id))
            scan_id = state.scan_id
            events = get_history(scan_id)
            tool_names = {e["payload"]["tool"] for e in events if e["type"] == "tool.called"}
            unknown = tool_names - registered_tools
            yield TestResult(
                test_id="F-08",
                test_name=f"Hardening tool calls ⊆ TOOLS registry ({profile_id})",
                test_category="functional",
                expected_outcome="every tool.called name is registered",
                actual_outcome=f"called={sorted(tool_names)}, unknown={sorted(unknown)}",
                result="pass" if not unknown else "fail",
                failure_mode=None if not unknown else "unknown_tool",
                metrics={"tool_call_accuracy": (len(tool_names) - len(unknown)) / max(1, len(tool_names))},
                input_fixture=profile_id,
            )
        except Exception as e:
            yield TestResult(
                test_id="F-08",
                test_name=f"Hardening tool registry coverage ({profile_id})",
                test_category="functional",
                expected_outcome="agent run + event capture",
                actual_outcome=f"{type(e).__name__}: {e}",
                result="error",
                failure_mode="agent_crash",
                input_fixture=profile_id,
            )
