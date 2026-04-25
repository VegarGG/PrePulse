"""UX (Week 3) and Business (Week 4) campaigns.

Per §8 of the validation plan, these campaigns require human participants
(SUS scores, recruiter-led usability sessions, customer interviews,
willingness-to-pay surveys). They are **not** automatable inside this
pipeline. This module logs an `inconclusive` row per campaign so the
master report still references them.

Detailed protocol artifacts live under:
  validation/fixtures/personas/         (Week 3)
  validation/fixtures/business/         (Week 4)
"""

from __future__ import annotations

from typing import Iterable

from validation.context import TestContext
from validation.result import TestResult


def run(ctx: TestContext) -> Iterable[TestResult]:
    yield TestResult(
        test_id="UX-01",
        test_name="Week 3 user testing campaign (3 personas, 5 task scripts, 6–8 participants)",
        test_category="ux",
        expected_outcome="task completion rates, SUS scores, think-aloud commentary captured",
        actual_outcome="not automatable; see validation/fixtures/personas/",
        result="inconclusive",
        failure_mode="not_automatable_in_pipeline",
        notes="Recruit participants matching SMB-owner / IT-manager / security-analyst personas.",
    )
    yield TestResult(
        test_id="BIZ-01",
        test_name="Week 4 business validation interviews (10–15 SMB owners or IT managers)",
        test_category="business",
        expected_outcome="pain-point validation rate, willingness-to-pay distribution, competitor gap notes",
        actual_outcome="not automatable; see validation/fixtures/business/",
        result="inconclusive",
        failure_mode="not_automatable_in_pipeline",
        notes="45-minute semi-structured interview script; pilot before running.",
    )
    yield TestResult(
        test_id="F-31",
        test_name="API endpoint authentication enforced",
        test_category="functional",
        expected_outcome="401/403 on unauthenticated calls",
        actual_outcome="prototype is unauthenticated by design (out of scope §3.4)",
        result="inconclusive",
        failure_mode="not_applicable_to_prototype",
        notes="Production-only requirement per validation plan §3.",
    )
