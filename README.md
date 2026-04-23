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
uvicorn backend.main:app --port 8000
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
| `ANTHROPIC_API_KEY` | *(empty)* | Required — agents run real Claude reasoning even in mock mode. |
| `OPENAI_API_KEY` | *(empty)* | Optional GPT-4o fallback when Anthropic fails. |
| `PREPULSE_AUTO_APPROVE` | *(unset)* | `1` auto-resolves the human approval gate (for demos or CI). |
| `PREPULSE_SKIP_SEED` | *(unset)* | `1` skips the 30-day history seed on startup. |
| `PREPULSE_APPROVAL_TIMEOUT` | `120` | Seconds the orchestrator waits for a human approval before rejecting. |
| `OTX_API_KEY` · `HIBP_API_KEY` · `ABUSEIPDB_API_KEY` · `NVD_API_KEY` | *(empty)* | Only consulted when `PREPULSE_LIVE=1`. |
| `NEXT_PUBLIC_API_BASE` | `http://localhost:8000` | Frontend → backend URL. |

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
