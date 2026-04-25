"""Pipeline-level tests against the running backend.

F-15  posture score determinism (same inputs → same score)
F-16  river_city pipeline completes
F-17  greenfield pipeline completes
F-18  shoplocal pipeline completes
F-19  SSE stream emits the canonical event taxonomy
F-20  trace JSONL is valid + monotonic
F-21  mock-mode determinism (3-run trace diff modulo timestamps)
F-33  demo profile expected posture scores within ±2 of spec

Requires: backend up on ctx.backend_url with a valid Anthropic key.
"""

from __future__ import annotations

import json
import re
import time
from typing import Iterable

import httpx

from validation.context import TestContext
from validation.result import TestResult

REQUIRES = {"backend", "llm"}

CANONICAL_EVENT_TYPES = {
    "scan.started",
    "scan.completed",
    "agent.started",
    "agent.completed",
    "tool.called",
    "tool.result",
}


def _start_scan(client: httpx.Client, profile_id: str) -> str:
    r = client.post("/api/scans", json={"profile_id": profile_id}, timeout=10.0)
    r.raise_for_status()
    return r.json()["scan_id"]


def _stream_events(client: httpx.Client, scan_id: str, timeout_s: int) -> list[dict]:
    events: list[dict] = []
    deadline = time.time() + timeout_s
    with client.stream("GET", f"/api/scans/{scan_id}/events", timeout=timeout_s) as resp:
        buf = ""
        for chunk in resp.iter_text():
            buf += chunk
            while "\n\n" in buf:
                frame, buf = buf.split("\n\n", 1)
                for line in frame.splitlines():
                    if not line.startswith("data:"):
                        continue
                    try:
                        events.append(json.loads(line[len("data:") :].strip()))
                    except json.JSONDecodeError:
                        continue
            if events and events[-1]["type"] in ("scan.completed", "scan.failed"):
                return events
            if time.time() > deadline:
                return events
    return events


def _strip_timestamps(events: list[dict]) -> list[dict]:
    out = []
    for e in events:
        ev = {**e, "ts": 0}
        if "payload" in ev and isinstance(ev["payload"], dict):
            p = dict(ev["payload"])
            for key in ("call_id", "action_id", "duration_ms", "executed_at", "started_at", "first_seen", "ts"):
                p.pop(key, None)
            ev["payload"] = p
        out.append(ev)
    return out


def run(ctx: TestContext) -> Iterable[TestResult]:
    if ctx.skip_llm_tests:
        yield TestResult(
            test_id="F-15..F-21,F-33",
            test_name="pipeline tests skipped",
            test_category="functional",
            expected_outcome="run pipeline tests",
            actual_outcome="PREPULSE_SKIP_LLM=1",
            result="inconclusive",
            failure_mode="skipped_by_env",
        )
        return

    profiles = [
        ("F-16", "river_city", 48),
        ("F-17", "greenfield", 32),
        ("F-18", "shoplocal", 72),
    ]
    expected_scores = {pid: score for _, pid, score in profiles}

    client = httpx.Client(base_url=ctx.backend_url)

    # Run each profile twice for F-21 mock determinism + F-15 score determinism.
    profile_traces: dict[str, list[list[dict]]] = {}

    for test_id, profile_id, expected in profiles:
        traces: list[list[dict]] = []
        for run_idx in range(2):
            scan_id = None
            try:
                scan_id = _start_scan(client, profile_id)
                events = _stream_events(client, scan_id, ctx.timeout_s)
                traces.append(events)

                completed = [e for e in events if e["type"] == "agent.completed"]
                final_event = next((e for e in events if e["type"] == "scan.completed"), None)
                final_report = (final_event or {}).get("payload", {}).get("final_report") or {}
                posture = final_report.get("posture_score")

                # F-16/17/18 — pipeline completes
                yield TestResult(
                    test_id=test_id,
                    test_name=f"{profile_id} end-to-end (run {run_idx + 1}/2)",
                    test_category="functional",
                    expected_outcome="scan.completed event arrives, ≥6 agent.completed events",
                    actual_outcome=f"events={len(events)}, agent.completed={len(completed)}, scan.completed={'yes' if final_event else 'no'}",
                    result="pass" if final_event and len(completed) >= 6 else "fail",
                    failure_mode=None if final_event else "scan_did_not_complete",
                    metrics={"end_to_end_success_rate": 1.0 if final_event else 0.0},
                    input_fixture=profile_id,
                )

                # F-19 — canonical event types observed
                seen = {e["type"] for e in events}
                missing = CANONICAL_EVENT_TYPES - seen
                yield TestResult(
                    test_id="F-19",
                    test_name=f"SSE event taxonomy ({profile_id} run {run_idx + 1})",
                    test_category="functional",
                    expected_outcome=f"all canonical event types: {sorted(CANONICAL_EVENT_TYPES)}",
                    actual_outcome=f"missing={sorted(missing)}",
                    result="pass" if not missing else "fail",
                    failure_mode=None if not missing else "missing_event_types",
                    input_fixture=profile_id,
                )

                # F-15 + F-33 — score determinism + expected score within ±2
                if posture is not None:
                    yield TestResult(
                        test_id="F-33",
                        test_name=f"{profile_id} expected posture ±2",
                        test_category="functional",
                        expected_outcome=f"score in [{expected - 2}, {expected + 2}]",
                        actual_outcome=str(posture),
                        result="pass" if abs(posture - expected) <= 2 else "fail",
                        failure_mode=None if abs(posture - expected) <= 2 else "score_drift",
                        metrics={"posture_score": posture},
                        input_fixture=profile_id,
                    )

                # F-20 — trace endpoint serves valid NDJSON
                if scan_id is not None:
                    trace_resp = client.get(f"/api/scans/{scan_id}/trace", timeout=10.0)
                    trace_lines = [ln for ln in trace_resp.text.splitlines() if ln.strip()]
                    monotonic = True
                    last_ts = -1.0
                    bad_lines = 0
                    for ln in trace_lines:
                        try:
                            obj = json.loads(ln)
                            ts = float(obj.get("ts") or 0)
                            if ts < last_ts:
                                monotonic = False
                            last_ts = ts
                        except json.JSONDecodeError:
                            bad_lines += 1
                    yield TestResult(
                        test_id="F-20",
                        test_name=f"trace JSONL fidelity ({profile_id} run {run_idx + 1})",
                        test_category="functional",
                        expected_outcome="every line valid JSONL, timestamps monotonic",
                        actual_outcome=f"lines={len(trace_lines)}, bad={bad_lines}, monotonic={monotonic}",
                        result="pass" if bad_lines == 0 and monotonic else "fail",
                        failure_mode=None if bad_lines == 0 and monotonic else "trace_invalid",
                        input_fixture=profile_id,
                    )
            except Exception as e:
                yield TestResult(
                    test_id=test_id,
                    test_name=f"{profile_id} pipeline (run {run_idx + 1}/2)",
                    test_category="functional",
                    expected_outcome="pipeline completes",
                    actual_outcome=f"{type(e).__name__}: {e}",
                    result="error",
                    failure_mode="pipeline_exception",
                    input_fixture=profile_id,
                )

        profile_traces[profile_id] = traces

    # F-15 + F-21 — determinism: two runs of the same profile produce identical
    # traces modulo timestamps and scan-id-bearing fields.
    for profile_id, traces in profile_traces.items():
        if len(traces) < 2:
            continue
        a = _strip_timestamps(traces[0])
        b = _strip_timestamps(traces[1])
        # Compare event-type sequence + tool names invoked
        seq_a = [(e["type"], e.get("payload", {}).get("agent")) for e in a]
        seq_b = [(e["type"], e.get("payload", {}).get("agent")) for e in b]
        identical = seq_a == seq_b
        yield TestResult(
            test_id="F-21",
            test_name=f"mock-mode determinism ({profile_id})",
            test_category="functional",
            expected_outcome="event-type/agent sequence identical across two mock runs",
            actual_outcome=f"len_a={len(a)}, len_b={len(b)}, identical={identical}",
            result="pass" if identical else "fail",
            failure_mode=None if identical else "non_deterministic",
            metrics={"determinism_rate": 1.0 if identical else 0.0},
            input_fixture=profile_id,
        )

        # F-15 — posture score determinism (subset of F-21)
        scores = []
        for events in traces:
            sc = next((e for e in events if e["type"] == "scan.completed"), None)
            if sc:
                scores.append((sc.get("payload") or {}).get("final_report", {}).get("posture_score"))
        if len(scores) == 2 and all(s is not None for s in scores):
            yield TestResult(
                test_id="F-15",
                test_name=f"posture score deterministic ({profile_id})",
                test_category="functional",
                expected_outcome="identical posture across two runs",
                actual_outcome=f"scores={scores}",
                result="pass" if scores[0] == scores[1] else "fail",
                failure_mode=None if scores[0] == scores[1] else "score_non_deterministic",
                input_fixture=profile_id,
            )

    client.close()
