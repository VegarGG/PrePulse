# PrePulse — Prototype v0.2.0

Preemptive, agentic-AI cybersecurity intelligence for small and mid-market
organizations. A six-agent fleet — Intelligence, Validator, Hardening,
Investigator, Remediator, Supervisor — surveys the external threat landscape,
validates exploit surface, stages defensive actions, and gates destructive
ones behind human approval.

Built for **MG-9781 — Beyond Data: GenAI-Driven Business Strategy &
Reinvention · NYU Tandon** by Ziwei Huang, Yunlong Chai, Xuanwei Fan, and
Zonghui Wu. See [`PrePulse_Prototype_Architecture_v2.md`](PrePulse_Prototype_Architecture_v2.md)
for the full product spec.

## What's demonstrated

- **Real LLM reasoning** (Claude Sonnet 4.6) for Intelligence, Validator,
  Investigator, and Supervisor — same model that would power production.
- **Mock-first tool I/O**: threat-intel APIs (OTX, HIBP, AbuseIPDB, NVD) and
  MITRE ATT&CK retrieval all run offline against scripted fixtures by default.
- **Simulated defensive actions**: firewall blocks, IAM rotations, endpoint
  isolation, ticketing, email — every call is logged, nothing mutates real
  infrastructure.
- **Human-in-the-loop gate**: remediations at severity `high` / `critical`
  pause for explicit approval before executing.
- **Live SSE streaming** of the six-agent timeline into a Next.js 14 console.
- **Statistical dashboard** seeded with 30 days of deterministic synthetic
  history so it is never empty on first boot.

## Requirements

| Tool | Version |
|---|---|
| Python | 3.11.x |
| Node.js | 20.x LTS (23.x also works with an engine warning) |
| npm | ≥ 10 |

## One-time setup

```bash
cd prepulse

# Backend
python3.11 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip setuptools wheel
pip install -r backend/requirements.txt

# MITRE ATT&CK dataset (48 MB, downloaded once)
mkdir -p backend/data
curl -L -o backend/data/attack_enterprise.json \
  "https://raw.githubusercontent.com/mitre-attack/attack-stix-data/master/enterprise-attack/enterprise-attack.json"

# Frontend
cd frontend
npm install --legacy-peer-deps
cd ..

# Secrets
cp .env.example .env     # then fill ANTHROPIC_API_KEY
```

## Run the stack

Two terminals:

```bash
# terminal 1 — backend
source .venv/bin/activate
uvicorn backend.main:app --port 8001
```

You will see the startup banner:

```
╭──────────────────────────────────────────────────────────────╮
│  PrePulse v0.2.0  ·  ready                                    │
│  mode           : mock                                        │
│  demo profiles  : 3                                           │
│  mitre attck    : 835   techniques loaded                     │
│  scan store     : 120   historical scans seeded               │
╰──────────────────────────────────────────────────────────────╯
```

```bash
# terminal 2 — frontend
cd frontend && npm run dev
```

Then open http://localhost:3000.

`make dev` does both in parallel if you prefer (`make bootstrap` once for
first-time install).

## Routes

- `GET /api/health` — liveness + mode (mock | live)
- `GET /api/demo/profiles` — the three scripted demo profiles
- `POST /api/scans` — start a scan (body: `{profile_id}` or `{custom_profile}`)
- `GET /api/scans` — history list
- `GET /api/scans/{id}` — full PipelineState
- `GET /api/scans/{id}/events` — Server-Sent Events stream
- `POST /api/scans/{id}/approve` — resolve a pending action (approve)
- `POST /api/scans/{id}/reject` — resolve a pending action (reject)
- `GET /api/scans/{id}/trace` — downloadable NDJSON reasoning log
- `GET /api/dashboard/metrics` — rolling KPIs + 30-day series

Frontend pages: `/` (landing) · `/run/[scanId]` (live console) · `/dashboard`
· `/history` · `/trace/[scanId]` · `/about`.

## Demo script (5 minutes)

See §29 of `PrePulse_Prototype_Architecture_v2.md` for the minute-by-minute
talking points. The short version:

1. Open landing → click **River City Financial Services**.
2. `/run/<id>` opens; watch the AgentTimeline animate through Intelligence,
   Validator & Hardening (parallel), then Investigator.
3. Action-approval modal appears during Remediator; click **Approve &
   execute**.
4. PostureGauge lands around 48 (Grade D), executive briefing renders, the
   dashboard tile updates on return.
5. Click **Dashboard** → KPIs + posture trend + severity bars +
   actions-by-kind + top tactics are already populated from the seed.
6. Click **History** → three scans listed.
7. Click any scan's **Trace** link → downloadable NDJSON reasoning log.

## Configuration

`.env` (gitignored) controls mode and credentials. Any of these can be
overridden by exporting shell env vars.

| Variable | Default | Purpose |
|---|---|---|
| `PREPULSE_LIVE` | `0` | `1` switches tools from scripted mocks to real APIs. |
| `PREPULSE_API_PROVIDER` | `0` | LLM provider chain: `0`=Anthropic, `1`=OpenAI, `2`=DeepSeek. The chosen index runs first; the others auto-fall-back via `with_fallbacks` if the chosen one errors. Providers without a key are skipped. Accepts a name too (e.g. `deepseek`). |
| `ANTHROPIC_API_KEY` / `ANTHROPIC_MODEL` | *(empty)* / `claude-sonnet-4-6` | Provider 0. Default model overridable. |
| `OPENAI_API_KEY` / `OPENAI_MODEL` | *(empty)* / `gpt-4o` | Provider 1. |
| `DEEPSEEK_API_KEY` / `DEEPSEEK_MODEL` / `DEEPSEEK_BASE_URL` | *(empty)* / `deepseek-v4-flash` / `https://api.deepseek.com/v1` | Provider 2. OpenAI-compatible, served via `langchain_openai.ChatOpenAI` with a custom `base_url`. |
| `PREPULSE_KB_LOW_THRESHOLD` / `PREPULSE_KB_HIGH_THRESHOLD` | `0.35` / `0.65` | Chatbot similarity gate (raised from 0.25/0.50 after validation showed 7/30 off-topic questions slipping past 0.25). |
| `HUGGINGFACE_API_TOKEN` | *(empty)* | Required for the chatbot's embedding gate. Fine-grained token with "Inference Providers" scope. |
| `PREPULSE_AUTO_APPROVE` | *(unset)* | `1` auto-resolves the human approval gate (for demos or CI). |
| `PREPULSE_SKIP_SEED` | *(unset)* | `1` skips the 30-day history seed on startup. |
| `PREPULSE_APPROVAL_TIMEOUT` | `120` | Seconds the orchestrator waits for a human approval before rejecting. |
| `OTX_API_KEY` · `HIBP_API_KEY` · `ABUSEIPDB_API_KEY` · `NVD_API_KEY` | *(empty)* | Only consulted when `PREPULSE_LIVE=1`. |
| `NEXT_PUBLIC_API_BASE` | `http://localhost:8001` | Frontend → backend URL. |

## Tests

```bash
# Fast suite — no LLM, no network
.venv/bin/pytest tests/test_tools.py tests/test_scoring.py tests/test_safety.py tests/test_api.py \
    --deselect tests/test_orchestrator.py::test_agent_in_isolation \
    --deselect tests/test_api.py::test_full_scan_river_city_integration

# Full LLM-dependent suite (requires ANTHROPIC_API_KEY, ~10 min, ~$2 in API calls)
.venv/bin/pytest tests/
```

Known-good counts: **39** tool/scoring · **21** safety · **12** API (non-integration) ·
**18** agent-isolation · **1** full-scan integration.

## Known deviations from the architecture spec

See [`SPEC_DEVIATIONS.md`](SPEC_DEVIATIONS.md) for the running log.

## Validation campaign — brief

Implementing the auto-runnable subset of `PrePulse_Validation_Testing_Plan.md`
under [`validation/`](validation/). Standalone runner; per-test JSONL with the
plan's §5.1 schema; combined `all_runs.jsonl` per campaign.

**Headline (281 results across the F-01..F-35 surface):**

| Result | Count | Note |
|---|---:|---|
| pass | **186** | majority of the deterministic + in-process surface |
| fail | 18 | all prototype-side (see below) |
| error | 3 | one chat request, one judge crash, one agent crash |
| inconclusive | 74 | almost entirely Anthropic rate-limit during the chatbot run |

**Tests at 100% pass-rate:** F-01/04/07/10/13 (75/75 schema conformance),
F-05 (MITRE ids), F-08 (tool registry), F-12 (Remediator routing),
F-15 (posture determinism in-process), F-19 (SSE event taxonomy),
F-20 (trace JSONL fidelity), F-22 (frontend routes), F-25 (trace bytes
stable), F-28 (no capability hallucination, 21/21), F-32 (LLM fallback
wired), F-34 (schema rejection), F-35 (injection canaries 14/14).

**Real prototype-side findings the campaign surfaced:**

- **F-33 / F-18 — posture-score drift.** LLM-driven Hardening agent
  consistently over-credits `risk_reduction_estimate`, pushing greenfield
  posture from spec=32 → 47, shoplocal 72 → 99. The high score skips
  Remediator (§11 conditional route) → only 5 agents fire (test required
  ≥6). Recommend tightening Hardening's prompt cap or `services/scoring.py`
  weights.
- **F-21 — LLM non-determinism.** Same profile, two runs, event
  sequences differ by 1 event. Temperature 0.2 isn't 0; mock-mode
  determinism (plan §2.5.1) is not achievable without `temperature=0`.
- **F-27 — chatbot off-topic refusal at 76% (target 90%).** 7/30 off-topic
  questions slipped the similarity gate. Bump `PREPULSE_KB_LOW_THRESHOLD`
  upward and/or add canonical-refusal phrasing into the system prompt.
- **F-02 — one CVE hallucinated from prose.** Intelligence agent on
  greenfield cited `CVE-2022-41040` (real CVE mentioned inside an OTX
  pulse description, but absent from the structured NVD fixture).
  Acceptable in mock mode; would resolve in live mode.

**Pipeline-side bugs found during the run, fixed in-flight:**

1. Runner didn't call `load_dotenv()` — agents couldn't see the API key
   and 84 tests crashed with "Could not resolve authentication".
2. F-26 LLM-as-judge silently returned `0` on errors; rate-limited judge
   runs all looked like wrong answers. Now returns `None` → `inconclusive`.
3. F-26 / F-29 conflated chatbot HTTP 502 with "wrong answer" / "successful
   injection". Now: 5xx → `inconclusive`, excluded from rate denominators.
   F-29 success rate fell from misreported 76% to 11% on evaluable prompts.
4. F-29 classifier missed natural-language refusals like *"I'm not able
   to do that…"*. Added a `REFUSAL_PHRASES` list.

**Final artifacts:**

- [`validation/runs/FINAL_combined/all_runs.jsonl`](validation/runs/FINAL_combined/all_runs.jsonl) — 281 rows, every pass + fail + inconclusive in one chronological file
- [`validation/reports/FINAL_combined_report.md`](validation/reports/FINAL_combined_report.md) — full breakdown with §7 metrics, Wilson-CI commentary, prioritised recommendations
- [`validation/README.md`](validation/README.md) — how to re-run

**To re-run:**
```bash
.venv/bin/python -m validation.runner --campaign $(date +%Y%m%d_%H%M%S)
```
Wall time ≈ 55 min; cost ≈ $2–5 in Anthropic calls per campaign.

UX (Week 3) and Business (Week 4) campaigns from the plan are scaffolded
under `validation/fixtures/personas/` and `validation/fixtures/business/`
but are **human-driven**, not in this auto run.
