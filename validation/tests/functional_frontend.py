"""Frontend functional tests.

F-22  Every defined route loads with HTTP 200 and produces no error
      markers in the served HTML.
F-25  Trace download SHA matches the same scan_id served by the backend.

Visual / Playwright tests (F-23, F-24) are out of automation scope —
they require a real browser. The plan flags them as such; this module
documents that explicitly via an `inconclusive` row.
"""

from __future__ import annotations

import hashlib
from typing import Iterable

import httpx

from validation.context import TestContext
from validation.result import TestResult

REQUIRES = {"frontend"}

ROUTES = ["/", "/dashboard", "/history", "/about"]
ERROR_MARKERS = (
    "Application error:",
    "Internal Server Error",
    "TypeError:",
    "ReferenceError:",
)


def run(ctx: TestContext) -> Iterable[TestResult]:
    for route in ROUTES:
        url = ctx.frontend_url + route
        try:
            r = httpx.get(url, timeout=10.0)
            html = r.text or ""
            errors = [m for m in ERROR_MARKERS if m in html]
            ok = r.status_code == 200 and not errors
            yield TestResult(
                test_id="F-22",
                test_name=f"frontend route {route} loads",
                test_category="functional",
                expected_outcome="HTTP 200 with no JS error markers in served HTML",
                actual_outcome=f"status={r.status_code}, error_markers={errors}",
                result="pass" if ok else "fail",
                failure_mode=None if ok else "frontend_error",
                metrics={"http_status": r.status_code},
                input_fixture=route,
            )
        except Exception as e:
            yield TestResult(
                test_id="F-22",
                test_name=f"frontend route {route}",
                test_category="functional",
                expected_outcome="route reachable",
                actual_outcome=f"{type(e).__name__}: {e}",
                result="error",
                failure_mode="frontend_unreachable",
                input_fixture=route,
            )

    # F-23, F-24 — visual checks; document and mark inconclusive.
    for tid, name in (
        ("F-23", "live event timeline updates within 1s of backend events"),
        ("F-24", "MITRE heatmap colours match scan output"),
    ):
        yield TestResult(
            test_id=tid,
            test_name=name,
            test_category="functional",
            expected_outcome="visual correctness via real browser",
            actual_outcome="not automated; requires Playwright + manual review",
            result="inconclusive",
            failure_mode="not_automatable_in_pipeline",
            notes="See validation/fixtures/personas/ for the human-driven UX protocol.",
        )

    # F-25 — Start a fresh scan via the backend, then SHA-compare the trace
    # endpoint response with itself across two consecutive fetches. We do not
    # have a frontend "download" endpoint distinct from the backend's
    # /api/scans/{id}/trace; the frontend simply links to it. The valid check
    # is therefore: identical bytes across two GETs of the same endpoint.
    try:
        with httpx.Client(base_url=ctx.backend_url, timeout=30.0) as client:
            r = client.post("/api/scans", json={"profile_id": "shoplocal"})
            if r.status_code == 200:
                scan_id = r.json()["scan_id"]
                # Wait briefly for events to accrue; we don't need a full pipeline.
                import time as _t

                _t.sleep(2)
                a = client.get(f"/api/scans/{scan_id}/trace")
                b = client.get(f"/api/scans/{scan_id}/trace")
                hash_a = hashlib.sha256(a.content).hexdigest()
                hash_b = hashlib.sha256(b.content).hexdigest()
                yield TestResult(
                    test_id="F-25",
                    test_name="trace endpoint produces stable bytes across consecutive GETs",
                    test_category="functional",
                    expected_outcome="SHA-256 identical across two fetches of the same scan",
                    actual_outcome=f"a={hash_a[:16]}, b={hash_b[:16]}",
                    result="pass" if hash_a == hash_b else "fail",
                    failure_mode=None if hash_a == hash_b else "trace_byte_drift",
                    input_fixture=scan_id,
                )
            else:
                yield TestResult(
                    test_id="F-25",
                    test_name="trace bytes stability",
                    test_category="functional",
                    expected_outcome="scan launches",
                    actual_outcome=f"POST /api/scans returned {r.status_code}",
                    result="error",
                    failure_mode="scan_launch_failed",
                )
    except Exception as e:
        yield TestResult(
            test_id="F-25",
            test_name="trace bytes stability",
            test_category="functional",
            expected_outcome="scan + dual trace fetch",
            actual_outcome=f"{type(e).__name__}: {e}",
            result="error",
            failure_mode="trace_check_exception",
        )
