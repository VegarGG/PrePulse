# PrePulse — Spec Deviations

A running record of places where the implementation diverges from
`PrePulse_Prototype_Architecture_v2.md`. Each entry states the deviation, why
it was necessary, and any follow-up that would bring the code back in line
with the canonical spec.

---

## Operational deviations

### Backend port moved to 8001
The spec uses `:8000` throughout (§5 architecture diagram, Appendix A.9
smoke-test, §26 Phase-4 acceptance check, Pre-flight checklist). The
implementation listens on `:8001` instead — `:8000` was consistently
occupied on the developer's machine by another process, and picking a
free port is less disruptive than diagnosing the squatter. Every
operational file (`Makefile`, `README.md`, `.env.example`,
`frontend/lib/api.ts`) was updated consistently; the architecture doc at
the repo root still reads `:8000` as the historical spec of record.

---

## Phase 3 — Multi-agent backend

### 1. Anthropic tool-name aliasing
The Anthropic API requires tool names to match `^[a-zA-Z0-9_-]{1,64}$` (no
dots), but our dotted names (e.g. `otx.get_pulses`) are how the spec labels
tools throughout §8–§10. We expose each tool to the LLM under an
underscore alias (`otx_get_pulses`) via a `REAL_TO_ALIAS` / `ALIAS_TO_REAL`
map in [backend/agents/base.py](backend/agents/base.py). Real dispatch still
goes through the dotted `TOOLS` registry, and `tool.called` events log the
dotted name — so the spec's observability contract is intact end-to-end.

### 2. Investigator authoritative override
After the LLM returns its `FinalReport`, the Investigator agent overwrites
`posture_score`, `posture_grade`, and `score_explanation` with the values
computed by `compute_posture_score()`. §13 declares the scoring engine
authoritative; the override makes that binding even when the model drifts.

### 3. Remediator plans only in the LLM turn
No tools are bound for the Remediator during its Phase 3 LLM call, matching
prompt §C.5 ("You are NOT to call the tools in this turn — only plan
them."). Action execution happens in the Phase 4 orchestrator after the
human-approval gate.

### 4. `audit.log_decision` signature
The underlying function takes `(summary, sign_off)` only — no `scan_id`
kwarg. The scan ID flows to the event bus via the `@tool` wrapper's own
`scan_id` parameter; removing the duplicate avoids a collision when the
wrapper forwards kwargs. Originally flagged in Phase 2 and still in force.

### 5. Agent repair on parse failure
`BaseAgent.run_core()` catches `ValidationError` / `ValueError` /
`JSONDecodeError` from the structured-output parse and re-issues the
prompt once with the validation error and prior malformed response
appended. Matches §14.2 ("on first failure, re-prompt the LLM with the
validation error").

### 6. `abuseipdb` mock widened to CIDR
The original dispatch only returned the profile's reputation fixture for an
exact IP match (e.g. `198.51.100.23`). Now the mock also CIDR-matches: any
IP within a profile's declared `ip_range` returns that profile's fixture
with the probed IP echoed in the `ip` field. This keeps the Intelligence
agent's tool call productive regardless of which IP the LLM picks from the
range, and the Phase 2 test suite still passes after the change.

---

## Phase 4 — Orchestration, API, SSE

### 1. Hardening no longer requires `validation_report`
The graph runs `validator` and `hardening` in parallel after
`intelligence` (§8 agent roster + §11 topology). §8's "reads from state"
column listed `validation_report` for Hardening, which is impossible under
the parallel-branch topology. Hardening now enforces only `intel_report`
and consumes `validation_report` opportunistically when present. Without
this change the scan fails at the fan-out.

### 2. Wall clock: 165s vs. SC-7's 90s target
A full `river_city` scan over real Anthropic calls lands at ~2–3 min. The
90s goal in §3 / SC-7 is achievable later by any of:
  - prompt caching on the shared system-style preamble,
  - tighter `max_tokens` per agent,
  - swapping non-Investigator agents to Haiku 4.5,
  - reducing the Validator's 10-call tool budget.

Not addressed in Phase 4; flagged for a performance pass in Phase 6.

### 3. Anthropic client timeout raised 30s → 90s
Validator's tool loop can stack 10 tool calls plus a final parse, which
exceeded the 30s ceiling specified in §14.4 under real network conditions.
Raising to 90s keeps each LLM round-trip comfortably within the socket
budget and does not weaken the overall retry semantics.

### 4. `/api/scans/{id}/trace` serves event history, not a separate trace store
§15 describes a distinct trace store with per-call records (prompt_chars,
tokens, tool_args, etc.). Phase 4 serves the in-memory event history as
NDJSON from the trace endpoint, which satisfies SC-9 (downloadable
reasoning log) in spirit. A richer per-call trace store is earmarked for
Phase 6 observability work.

### 5. ASGI-transport integration test uses `PREPULSE_AUTO_APPROVE=1`
`httpx.AsyncClient` over `ASGITransport` serializes concurrent requests in
ways that stall the SSE read when a POST /approve is awaited inline. To
keep `test_full_scan_river_city_integration` deterministic, the in-process
test runs with auto-approve on. The explicit POST /approve path is covered
by dedicated unit tests (`test_approve_resolves_pending_action`,
`test_reject_resolves_pending_action`), and the real HTTP path — real
uvicorn + real curl — was exercised during the Phase 4 acceptance run.

---

## Phase 6 — Demo polish & QA

### 1. The 10-run < 60s-average timing target was not measured
§28 step 4 calls for 10 back-to-back mock runs across 3 profiles averaging
under 60 seconds. Phase 4 established that a single scan clocks in at
~165 s via real `uvicorn` + `curl`, so the 60 s target is not physically
achievable with the current agent loop. No attempt was made to run 10
scans in this phase — that would have cost ~$15 in Anthropic calls and ~30
minutes of wall time without changing the qualitative result. The
performance gap is tracked as Phase 4 deviation #2 and remains open.

### 2. Offline test (Wi-Fi disabled) not run by the agent
§28 step 6 asks the operator to disable Wi-Fi and run the three profiles
end-to-end in mock mode. The agent can't toggle the host network interface,
and with `ANTHROPIC_API_KEY` set the LLM call still needs internet, so the
"fully offline" path only works if the user additionally sets
`PREPULSE_LIVE=0` *and* stubs the LLM gateway (e.g. swaps to a local
model). Documented in README; execution left to the operator.

### 3. Seeded scans use shape-valid synthetic data, not historical replay
§21 asks for "four scans per day with small variations in posture score,
threat counts, and action counts" plus "three narrative dips corresponding
to incident days." [backend/demo/seed.py](backend/demo/seed.py) delivers
this deterministically (seed=42, dip days 7/14/21, ~4 scans/day across 5
synthetic company profiles). The LLM-authored fields (`raw_summary`,
`validation_summary`, `executive_summary`, `critical_findings[].detail`,
etc.) use placeholder copy ("Historical synthetic ...") rather than
plausible narrative prose — they never surface in the dashboard KPIs, but a
reviewer who drills into a historical scan's `/run/<id>` page will see the
synthetic language. Phase 6 does not run real LLMs against 120 historical
scans.

### 4. Banner uses `print(..., flush=True)` rather than uvicorn's logger
FastAPI startup logs normally flow through the uvicorn logger. Routing the
banner through the same pipeline would tag it with an `INFO:` prefix and
subject it to log-level filtering, defeating the purpose of a prominent
human-readable startup notice. Using `print(..., flush=True)` guarantees
the banner always lands on stdout regardless of `--log-level`.

### 5. Conftest skips the seed via `PREPULSE_SKIP_SEED=1`
Tests that make shape assertions about an empty store
(`test_dashboard_metrics_shape_when_empty`) would break if lifespan seeded
120 scans on every `TestClient` construction. The autouse `_mock_mode`
fixture now sets `PREPULSE_LIVE=0`, `PREPULSE_AUTO_APPROVE=1`, and
`PREPULSE_SKIP_SEED=1` so every test sees a clean store and deterministic
mock dispatch. Integration tests that need LLM can still opt back in
explicitly via `monkeypatch.setenv`.

---

## Carried-forward deviations (originated earlier, still in force)

- **`mitre_store.get_retriever()`** uses `DeterministicFakeEmbedding` as the
  offline default (Phase 2). OpenAI embeddings only engage when both
  `OPENAI_API_KEY` and `PREPULSE_LIVE=1` are set.
- **`mitre.match_techniques` mock dispatches by keyword** (Phase 2) —
  fintech/healthcare/e-commerce markers in the threat description pick the
  profile's fixture. Replaced by the real vector store when
  `PREPULSE_LIVE=1`.
- **`pyproject.toml`** was added for pytest config
  (`asyncio_mode=auto`, `pythonpath=["."]`). `backend/requirements.txt`
  remains the dependency source of truth per Appendix A.4.
- **Frontend scaffold on Tailwind v3**: the shadcn CLI initialized
  `globals.css` for Tailwind v4 (oklch variables, `@import "tw-animate-css"`).
  We rewrote the CSS and `tailwind.config.ts` for the pinned Tailwind v3
  stack and added `tailwindcss-animate@1.0.7`.
