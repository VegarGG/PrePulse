# PrePulse Validation Pipeline

Implements the automatable subset of `PrePulse_Validation_Testing_Plan.md`.
Standalone Python (no pytest); each test module exports
`def run(ctx) -> Iterable[TestResult]` and the runner aggregates
JSONL logs per the plan's §5.1 schema.

## Quick start

```bash
# from prepulse/ root, with .venv active and backend running on :8001
.venv/bin/python -m validation.runner --campaign baseline_$(date +%Y%m%d)

# subset of modules
.venv/bin/python -m validation.runner --modules functional_safety chatbot_security

# list available modules
.venv/bin/python -m validation.runner --list
```

Outputs:
```
validation/runs/<campaign>/<category>.jsonl     # raw JSONL log per category
validation/reports/<campaign>_report.md         # aggregated Markdown report
```

## Test coverage matrix (vs. plan §4)

| Plan ID | Module | Notes |
|---|---|---|
| F-01 / F-04 / F-07 / F-10 / F-13 | `functional_schemas` | Pydantic-validates each agent's report across N runs |
| F-02 | `functional_citations` | CVE citations vs. demo NVD fixtures |
| F-03 | covered indirectly via F-21 | mock-mode determinism |
| F-05 | `functional_citations` | MITRE technique IDs vs. fixture set |
| F-06 | `functional_citations` *(extension)* | needs gold-standard scenarios — see fixtures/gold_standard/ |
| F-08 | `functional_citations` | tool calls ⊆ TOOLS registry |
| F-09 | `functional_pipeline` *(via SSE action.pending events)* | implicit |
| F-11 | requires human raters | scaffolded, not auto |
| F-12 | `functional_safety` | route_after_investigator threshold |
| F-14 | requires correctness oracle | scaffolded only |
| F-15 | `functional_safety` (in-process) + `functional_pipeline` (live) | determinism |
| F-16 / F-17 / F-18 | `functional_pipeline` | end-to-end per profile |
| F-19 | `functional_pipeline` | SSE event taxonomy |
| F-20 | `functional_pipeline` | trace JSONL fidelity |
| F-21 | `functional_pipeline` | mock-mode determinism (2-run diff) |
| F-22 | `functional_frontend` | route HTTP 200 + no JS error markers |
| F-23 / F-24 | `functional_frontend` | logged as inconclusive (visual; needs Playwright) |
| F-25 | `functional_frontend` | SHA stability across two trace fetches |
| F-26 | `chatbot_quality` | LLM-as-judge over 50-question bank |
| F-27 | `chatbot_quality` | refusal classifier over 30 off-topic |
| F-28 | `chatbot_quality` | capability-hallucination heuristic over 20 |
| F-29 | `chatbot_security` | 30 adversarial prompts |
| F-30 | `chatbot_quality` | p50/p95/p99 latency over the merged bank |
| F-31 | `ux_business` | logged as not-applicable (no auth in prototype) |
| F-32 | `functional_safety` | static inspection of `backend.llm.get_llm` |
| F-33 | `functional_pipeline` | profile posture within ±2 of spec |
| F-34 | `functional_safety` | malformed-input rejection across 5 schemas |
| F-35 | `functional_safety` | injection canaries against InputValidator |

UX (Week 3) and Business (Week 4) campaigns from §8 are scaffolded under
`validation/fixtures/personas/` and `validation/fixtures/business/` —
they are deliberately **not** auto-runnable. The pipeline records one
`inconclusive` row per campaign with a pointer to the protocol.

## Environment knobs

| Env var | Default | Effect |
|---|---|---|
| `PREPULSE_BACKEND_URL` | `http://localhost:8001` | Where pipeline + chatbot tests probe |
| `PREPULSE_FRONTEND_URL` | `http://localhost:3000` | Where frontend route tests probe |
| `PREPULSE_SKIP_LLM` | unset | `1` to skip LLM-dependent modules |
| `PREPULSE_SKIP_FRONTEND` | unset | `1` to skip frontend module |
| `PREPULSE_USE_LLM_JUDGE` | `1` | `0` to disable LLM-as-judge for F-26 (then accuracy is unmeasured) |
| `PREPULSE_MODEL_VERSION` | `claude-sonnet-4-6` | Stamped into each TestResult for reproducibility |

Standard `ANTHROPIC_API_KEY` and `HUGGINGFACE_API_TOKEN` from the
backend's `.env` are also required — the LLM-as-judge in F-26 calls
Claude directly, and the chatbot tests call the running backend which
needs both keys.

## Cost estimate per campaign

A full run hits the LLM many times:

- F-01..F-13 (5 agents × 3 profiles × 2 runs = 30 agent runs) — ~$0.50–1.00
- F-15..F-21,F-33 (3 profiles × 2 full pipeline runs = 6 scans, ~6 agents each) — ~$1.00–2.00
- F-26..F-30 (50 + 30 + 20 = 100 chatbot calls + 50 LLM-as-judge calls) — ~$0.50–1.00
- F-29 (30 adversarial chatbot calls) — ~$0.10–0.30

**Total: roughly $2–5 per campaign.** Wall time: 25–45 min depending
on Anthropic latency.

## Where to start when reviewing

1. Sanity-import everything:

   ```bash
   .venv/bin/python -c "from validation.runner import _discover_modules, _load; mods = _discover_modules(); [(_load(m), print('  ✓', m)) for m in mods]"
   ```

2. Single-module dry run (no LLM cost):

   ```bash
   PREPULSE_SKIP_LLM=1 .venv/bin/python -m validation.runner \
     --campaign smoke --modules functional_safety
   cat validation/runs/smoke/functional.jsonl | jq -c .
   cat validation/reports/smoke_report.md
   ```

3. Full functional-only campaign:

   ```bash
   .venv/bin/python -m validation.runner \
     --campaign functional --modules functional_schemas functional_citations functional_safety
   ```

## Fixtures the team should grow

- `fixtures/gold_standard/` — only 2 example scenarios shipped; plan
  asks for 15 expert-authored. ~2 person-days.
- `fixtures/chatbot/product_questions.json` — 50 seeded; rubrics are
  short. Refine over time as the chatbot improves.
- `fixtures/chatbot/adversarial_prompts.json` — 30 seeded; expand
  by adding new categories as the team learns from real attacks.

## Plan sections explicitly **not** automated here

- §3 (full-scale product testing — load, multi-tenant, red team, SOC 2) — pre-production work.
- §8 Week 3 (user testing) — protocol scaffolded, sessions are human.
- §8 Week 4 (business interviews + Van Westendorp) — protocol scaffolded.
- Inter-rater κ (§7.2) — single auto-rater; needs human + a reconciler to compute properly.

These sections appear in the master report as `inconclusive` rows so
they remain visible.
