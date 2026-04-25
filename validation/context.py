"""Shared context object passed to every test module.

Captures the runtime configuration (backend URL, fixture paths, run dir)
so tests don't have to recompute it themselves. The same object also
threads through to the JsonlEmitter.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from validation.result import JsonlEmitter

ROOT = Path(__file__).resolve().parents[1]
VALIDATION_DIR = ROOT / "validation"
FIXTURES_DIR = VALIDATION_DIR / "fixtures"
RUNS_DIR = VALIDATION_DIR / "runs"
REPORTS_DIR = VALIDATION_DIR / "reports"


@dataclass
class TestContext:
    backend_url: str = field(default_factory=lambda: os.getenv("PREPULSE_BACKEND_URL", "http://localhost:8001"))
    frontend_url: str = field(default_factory=lambda: os.getenv("PREPULSE_FRONTEND_URL", "http://localhost:3000"))
    campaign_name: str = ""
    runs_per_test: int = 5  # default; F-01..F-13 spec is 30, override per-test
    seed_runs: int = 30
    e2e_runs: int = 10  # full pipeline runs are expensive
    chatbot_runs_factual: int = 50
    chatbot_runs_off_topic: int = 30
    chatbot_runs_capability: int = 20
    chatbot_runs_adversarial: int = 30
    timeout_s: int = 600
    use_llm_judge: bool = field(default_factory=lambda: os.getenv("PREPULSE_USE_LLM_JUDGE", "1") == "1")
    skip_llm_tests: bool = field(default_factory=lambda: os.getenv("PREPULSE_SKIP_LLM", "0") == "1")
    skip_frontend_tests: bool = field(default_factory=lambda: os.getenv("PREPULSE_SKIP_FRONTEND", "0") == "1")

    # populated by the runner before each campaign
    emitter: JsonlEmitter | None = None
    campaign_dir: Path | None = None

    def fixture_path(self, *parts: str) -> Path:
        return FIXTURES_DIR.joinpath(*parts)
