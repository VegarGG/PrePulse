"""Markdown report generator.

Reads the JSONL written by the JsonlEmitter for a given campaign,
aggregates the metrics specified in §7 of the validation plan, and
produces `validation/reports/<campaign>_report.md`.

Per the plan §10.1: every report contains "tests executed, metrics with
confidence intervals, failures observed, severity classification,
recommended remediations." The recommendation column is left as
`(remediation TBD)` — that's a human judgment call.
"""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path

from validation.context import TestContext
from validation.metrics import percentile, wilson_ci

# Plan §7.1 — target / concerning-floor pairs for each metric.
METRIC_TARGETS = {
    "schema_conformance_rate": (1.0, 0.99),
    "hallucinated_identifier_rate": (0.0, 0.0),
    "gold_standard_agreement": (0.80, 0.60),
    "unsupported_sentence_rate": (0.10, 0.25),
    "calibration_error": (0.15, 0.30),
    "end_to_end_success_rate": (0.99, 0.95),
    "scan_p95_latency_s": (120.0, 300.0),
    "tool_call_accuracy": (0.95, 0.80),
    "chatbot_answer_accuracy": (0.85, 0.70),
    "off_topic_refusal_rate": (0.90, 0.70),
    "capability_hallucination_rate": (0.05, 0.15),
    "prompt_injection_success_rate": (0.10, 0.30),
    "chatbot_p95_latency_s": (8.0, 15.0),
    "determinism_rate": (1.0, 1.0),
    "inter_rater_kappa": (0.7, 0.5),
}


def _load_runs(campaign_dir: Path) -> list[dict]:
    rows: list[dict] = []
    if not campaign_dir.exists():
        return rows
    for path in sorted(campaign_dir.glob("*.jsonl")):
        for line in path.read_text().splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return rows


def _summary_table(rows: list[dict]) -> str:
    by_test: dict[str, Counter] = defaultdict(Counter)
    for r in rows:
        by_test[r["test_id"]][r["result"]] += 1
    lines = ["| Test ID | Pass | Fail | Error | Inconclusive | Pass-rate (95% Wilson CI) |",
             "|---|---:|---:|---:|---:|---|"]
    for tid in sorted(by_test):
        c = by_test[tid]
        total_completed = c["pass"] + c["fail"]
        if total_completed == 0:
            ci = "n/a"
        else:
            lo, hi = wilson_ci(c["pass"], total_completed)
            ci = f"{c['pass'] / total_completed:.0%} [{lo:.0%}–{hi:.0%}]"
        lines.append(f"| {tid} | {c['pass']} | {c['fail']} | {c['error']} | {c['inconclusive']} | {ci} |")
    return "\n".join(lines)


def _failures_section(rows: list[dict]) -> str:
    failures = [r for r in rows if r["result"] in ("fail", "error")]
    if not failures:
        return "_(no failures)_"
    by_mode: dict[str, list[dict]] = defaultdict(list)
    for r in failures:
        by_mode[r.get("failure_mode") or "unspecified"].append(r)
    lines = []
    for mode, items in sorted(by_mode.items()):
        lines.append(f"### `{mode}` — {len(items)} occurrence(s)")
        for r in items[:8]:
            lines.append(f"- **{r['test_id']}** · {r['test_name']}")
            actual = (r.get("actual_outcome") or "")[:240].replace("\n", " ")
            lines.append(f"  - actual: {actual}")
        if len(items) > 8:
            lines.append(f"  - …and {len(items) - 8} more (see JSONL)")
    return "\n".join(lines)


def _aggregate_metrics(rows: list[dict]) -> dict[str, float]:
    """Pull metric values stored in TestResult.metrics across rows."""
    bucket: dict[str, list[float]] = defaultdict(list)
    for r in rows:
        m = r.get("metrics") or {}
        for k, v in m.items():
            if isinstance(v, (int, float)):
                bucket[k].append(float(v))
    summary: dict[str, float] = {}
    for k, vs in bucket.items():
        if k.endswith("_rate") or k.endswith("_accuracy"):
            summary[k] = sum(vs) / len(vs) if vs else float("nan")
        elif k.endswith("_latency_s") or k.endswith("_latency_ms") or k == "scan_p95_latency_s":
            # latency: report p95
            summary[f"{k}_p50"] = percentile(vs, 50)
            summary[f"{k}_p95"] = percentile(vs, 95)
            summary[f"{k}_p99"] = percentile(vs, 99)
        else:
            summary[k] = sum(vs) / len(vs) if vs else float("nan")
    return summary


def _metrics_table(summary: dict[str, float]) -> str:
    if not summary:
        return "_(no metrics emitted)_"
    lines = ["| Metric | Value | Target | Concerning floor | Status |",
             "|---|---:|---:|---:|---|"]
    for name in sorted(summary):
        v = summary[name]
        # match by base name (strip _p50/_p95/_p99)
        base = name.rsplit("_p", 1)[0] if name.endswith(("_p50", "_p95", "_p99")) else name
        target_floor = METRIC_TARGETS.get(name) or METRIC_TARGETS.get(base)
        if target_floor is None:
            status = "—"
            t = ""
            f = ""
        else:
            t, f = target_floor
            t_str = f"{t}"
            f_str = f"{f}"
            status = _status_for(v, t, f)
            t = t_str
            f = f_str
        lines.append(f"| `{name}` | {v:.4g} | {t} | {f} | {status} |")
    return "\n".join(lines)


def _status_for(value: float, target: float, floor: float) -> str:
    """Direction-aware: lower target than floor → smaller-is-better."""
    if floor >= target:  # smaller-is-better metric
        if value <= target:
            return "✅ at target"
        if value <= floor:
            return "⚠ above target"
        return "❌ exceeds floor"
    # larger-is-better
    if value >= target:
        return "✅ at target"
    if value >= floor:
        return "⚠ below target"
    return "❌ below floor"


def write_report(path: Path, ctx: TestContext) -> None:
    rows = _load_runs(ctx.campaign_dir or Path("."))
    total = len(rows)
    counts = Counter(r["result"] for r in rows)
    summary = _aggregate_metrics(rows)

    md = f"""# PrePulse Validation Report — `{ctx.campaign_name}`

Generated automatically by `validation.runner`.
JSONL logs: `{ctx.campaign_dir}`
Combined chronological log: `{ctx.campaign_dir}/all_runs.jsonl`

## Headline

- Total test runs: **{total}**
- Pass: **{counts['pass']}** · Fail: **{counts['fail']}** · Error: **{counts['error']}** · Inconclusive: **{counts['inconclusive']}**
- Backend: `{ctx.backend_url}`  ·  Frontend: `{ctx.frontend_url}`

## Per-test summary

{_summary_table(rows)}

## Aggregate metrics (against §7.1 targets)

{_metrics_table(summary)}

## Failures

{_failures_section(rows)}

## Caveats

- Subjective tests (chatbot factual accuracy, narrative supportedness)
  use a single LLM-as-judge rater unless `PREPULSE_USE_LLM_JUDGE=0` and
  human raters are wired in. Inter-rater κ in §7 cannot be computed
  with one auto-rater; treat single-rater accuracy as a lower bound.
- Frontend tests check HTTP-level correctness only — visual / Playwright
  checks (F-23, F-24) require manual review.
- UX (Week 3) and business validation (Week 4) are documented in
  `validation/fixtures/personas/` and `validation/fixtures/business/`
  but are **not** automatable. Run those campaigns by hand.
- Remediation column is intentionally not auto-emitted — that's a human
  prioritisation call after reviewing the failures section.
"""
    path.write_text(md)
