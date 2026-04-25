"""TestResult dataclass + JSONL emitter (per §5.1 of the validation plan).

Every test run, pass or fail, produces one record on disk under
`validation/runs/<campaign>/<category>.jsonl`. The schema is intentionally
verbose so each line is reproducible against a known build.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import time
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Literal

Result = Literal["pass", "fail", "error", "inconclusive"]
Category = Literal["functional", "ux", "business", "adversarial"]


@dataclass
class TestResult:
    """One row in a JSONL log. Maps 1:1 to the validation-plan §5.1 schema."""

    test_id: str
    test_name: str
    test_category: Category
    expected_outcome: str
    actual_outcome: str
    result: Result
    failure_mode: str | None = None
    metrics: dict[str, Any] = field(default_factory=dict)
    rater_id: str = "auto"
    notes: str = ""
    rerun_of: str | None = None
    input_fixture: str | None = None
    # populated automatically by emit()
    run_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp_utc: str = field(default_factory=lambda: time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
    git_sha: str = ""
    model_version: str = ""
    prompt_hash: str = ""

    def __post_init__(self) -> None:
        if self.result in ("fail", "error") and not self.failure_mode:
            self.failure_mode = "unspecified"


_GIT_SHA_CACHE: str | None = None


def _git_sha() -> str:
    global _GIT_SHA_CACHE
    if _GIT_SHA_CACHE is not None:
        return _GIT_SHA_CACHE
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=Path(__file__).resolve().parents[1]
        ).decode().strip()
    except Exception:
        out = "unknown"
    _GIT_SHA_CACHE = out
    return out


def _prompt_hash(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()[:16]


class JsonlEmitter:
    """Append-only JSONL writer keyed to a campaign directory + category."""

    def __init__(self, campaign_dir: Path):
        self.campaign_dir = campaign_dir
        self.campaign_dir.mkdir(parents=True, exist_ok=True)
        self._buffers: dict[str, list[TestResult]] = {}

    def emit(self, r: TestResult) -> None:
        if not r.git_sha:
            r.git_sha = _git_sha()
        if not r.model_version:
            r.model_version = os.getenv("PREPULSE_MODEL_VERSION", "claude-sonnet-4-6")
        line = json.dumps(asdict(r), default=str) + "\n"
        # per-category file
        with (self.campaign_dir / f"{r.test_category}.jsonl").open("a") as fh:
            fh.write(line)
        # combined chronological log — one file with every pass and every
        # failure across every category, written as the run progresses so
        # a crash mid-campaign still leaves an audit trail.
        with (self.campaign_dir / "all_runs.jsonl").open("a") as fh:
            fh.write(line)
        self._buffers.setdefault(r.test_category, []).append(r)

    def all(self) -> list[TestResult]:
        out: list[TestResult] = []
        for v in self._buffers.values():
            out.extend(v)
        return out

    def by_test_id(self, test_id: str) -> list[TestResult]:
        return [r for r in self.all() if r.test_id == test_id]


def make_prompt_hash(*parts: str) -> str:
    """Build a stable prompt hash from one or more prompt fragments."""
    return _prompt_hash("\n---\n".join(parts))
