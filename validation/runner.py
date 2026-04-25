"""Validation campaign runner.

Each test module under `validation/tests/` exports:

    def run(ctx: TestContext) -> Iterable[TestResult]:
        ...

The runner discovers every module that defines `run`, executes them in
order, writes JSONL to `validation/runs/<campaign>/<category>.jsonl`,
aggregates metrics, and emits a Markdown report under
`validation/reports/<campaign>_report.md`.

Usage:
    python -m validation.runner                       # full campaign
    python -m validation.runner --modules functional_safety chatbot_security
    python -m validation.runner --campaign baseline   # named campaign

A test module may declare `REQUIRES = {"backend", "frontend", "llm"}`
at module level; the runner skips it if those services aren't reachable
(or `PREPULSE_SKIP_LLM=1` etc. is set) and logs an `inconclusive` result.
"""

from __future__ import annotations

import argparse
import importlib
import os
import pkgutil
import sys
import time
import traceback
from pathlib import Path
from typing import Iterable

import httpx
from dotenv import load_dotenv

# Load .env BEFORE importing any backend module so ANTHROPIC_API_KEY,
# HUGGINGFACE_API_TOKEN etc. are visible to the agents that test modules
# invoke in-process. Without this, ChatAnthropic instantiates with no
# key and every LLM call errors out as "Could not resolve authentication
# method".
load_dotenv(Path(__file__).resolve().parents[1] / ".env")

from validation.context import REPORTS_DIR, RUNS_DIR, TestContext
from validation.report import write_report
from validation.result import JsonlEmitter, TestResult


def _discover_modules() -> list[str]:
    import validation.tests as pkg

    names: list[str] = []
    for _, name, _ in pkgutil.iter_modules(pkg.__path__):
        if name.startswith("_"):
            continue
        names.append(name)
    return sorted(names)


def _load(module_name: str):
    return importlib.import_module(f"validation.tests.{module_name}")


def _backend_up(url: str, timeout: float = 2.0) -> bool:
    try:
        r = httpx.get(f"{url}/api/health", timeout=timeout)
        return r.status_code == 200
    except Exception:
        return False


def _frontend_up(url: str, timeout: float = 2.0) -> bool:
    try:
        r = httpx.get(url, timeout=timeout)
        return r.status_code == 200
    except Exception:
        return False


def run_campaign(
    campaign_name: str,
    module_names: list[str] | None = None,
    ctx_overrides: dict | None = None,
) -> Path:
    ctx = TestContext(**(ctx_overrides or {}))
    ctx.campaign_name = campaign_name
    ctx.campaign_dir = RUNS_DIR / campaign_name
    ctx.emitter = JsonlEmitter(ctx.campaign_dir)

    backend_up = _backend_up(ctx.backend_url)
    frontend_up = _frontend_up(ctx.frontend_url)

    print(f"[validation] campaign={campaign_name}")
    print(f"[validation] backend  {ctx.backend_url} → {'up' if backend_up else 'DOWN'}")
    print(f"[validation] frontend {ctx.frontend_url} → {'up' if frontend_up else 'DOWN'}")
    print(f"[validation] runs_dir = {ctx.campaign_dir}")

    modules = module_names or _discover_modules()
    print(f"[validation] running {len(modules)} module(s): {', '.join(modules)}")

    started = time.time()
    for name in modules:
        try:
            mod = _load(name)
        except Exception as e:
            ctx.emitter.emit(TestResult(
                test_id=f"MODULE-{name}",
                test_name=f"import {name}",
                test_category="functional",
                expected_outcome="module imports cleanly",
                actual_outcome=f"{type(e).__name__}: {e}",
                result="error",
                failure_mode="module_import_error",
                notes=traceback.format_exc(limit=4),
            ))
            continue

        requires = getattr(mod, "REQUIRES", set())
        skip_reason: str | None = None
        if "backend" in requires and not backend_up:
            skip_reason = "backend not reachable"
        if "frontend" in requires and not frontend_up:
            skip_reason = "frontend not reachable"
        if "llm" in requires and ctx.skip_llm_tests:
            skip_reason = "PREPULSE_SKIP_LLM=1"
        if skip_reason:
            ctx.emitter.emit(TestResult(
                test_id=f"MODULE-{name}",
                test_name=f"module {name} prerequisites",
                test_category="functional",
                expected_outcome="prerequisites met",
                actual_outcome=skip_reason,
                result="inconclusive",
                failure_mode="prerequisites_not_met",
            ))
            continue

        run_fn = getattr(mod, "run", None)
        if run_fn is None:
            continue

        print(f"[validation]   ▶ {name}")
        t0 = time.time()
        try:
            results: Iterable[TestResult] = run_fn(ctx)
            count = 0
            for r in results:
                ctx.emitter.emit(r)
                count += 1
            print(f"[validation]   ✓ {name} ({count} results, {time.time() - t0:.1f}s)")
        except Exception as e:
            ctx.emitter.emit(TestResult(
                test_id=f"MODULE-{name}",
                test_name=f"module {name} crashed",
                test_category="functional",
                expected_outcome="module run() returns without exception",
                actual_outcome=f"{type(e).__name__}: {e}",
                result="error",
                failure_mode="module_crash",
                notes=traceback.format_exc(limit=8),
            ))
            print(f"[validation]   ✗ {name} crashed: {e}")

    elapsed = time.time() - started
    print(f"[validation] all modules done in {elapsed:.1f}s")

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    report_path = REPORTS_DIR / f"{campaign_name}_report.md"
    write_report(report_path, ctx)
    print(f"[validation] report → {report_path}")
    return report_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="PrePulse validation campaign runner")
    parser.add_argument("--campaign", default=time.strftime("%Y-%m-%d_%H%M%S_baseline"))
    parser.add_argument("--modules", nargs="*", default=None,
                        help="Subset of modules to run (default: all)")
    parser.add_argument("--list", action="store_true", help="List discovered modules and exit")
    args = parser.parse_args(argv)

    if args.list:
        for m in _discover_modules():
            print(m)
        return 0

    run_campaign(args.campaign, args.modules)
    return 0


if __name__ == "__main__":
    sys.exit(main())
