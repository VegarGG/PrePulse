# Safety & Governance

PrePulse is built so that every potentially destructive decision is
either *deterministic* or *gated by a human*. The prototype exposes four
overlapping safety layers.

## 1. Input validation (prompt injection)

Every user-supplied profile field — company name, domain, tech stack — is
checked against a regex set that covers common prompt-injection patterns
("ignore previous instructions", "reveal your system prompt", chat-template
delimiters, etc.). Any match returns HTTP 400 with
`{error: "input_validation_failed", reason: "prompt_injection_suspected"}`
**before** any LLM call is made.

## 2. Deterministic scoring

The posture score (0–100) is computed by a deterministic Python function
that the Investigator agent must use as authoritative. Even if the LLM
drifts in its written reasoning, the score and grade are overwritten with
the engine's values before the report is returned to the client. Every
deduction is itemised and downloadable in the trace.

## 3. Human-in-the-loop approval gate

The Remediator pauses execution before any action with severity `high` or
`critical`. The pipeline emits an `action.pending` event, the UI renders
an approval modal showing the action kind, severity, and arguments, and
the orchestrator awaits an explicit click from the operator. Dismissing
the modal (X, Escape, click-outside) is treated as a reject so the scan
never hangs silently. There is a configurable timeout
(`PREPULSE_APPROVAL_TIMEOUT`, default 120 s) after which the gate
auto-rejects.

## 4. Reasoning transparency

Every LLM call, every tool call, and every parse step emits a typed event
to the in-memory event bus. The `/api/scans/{id}/trace` endpoint serves
the full event stream as NDJSON, downloadable from the UI. This is the
EU AI Act / SEC cyber-disclosure story for free: a complete, replayable
audit trail of how a decision was reached.

## What is *simulated* in the prototype

Three agents take action against the world: Hardening, Remediator, and
Supervisor. In production these would call real APIs (firewall, IAM,
EDR). In the prototype they call the same tool decorator stack but the
underlying functions sleep briefly, log to an audit store, and return a
shaped result that says `"simulated": true` and `"message": "Would block
198.51.100.23 at perimeter for 24h"`. Nothing mutates real
infrastructure.

The reasoning is real — same Claude Sonnet model that would power
production, same MITRE ATT&CK retrieval, same threat-intelligence
schemas. What is mocked is the *outbound side* against external systems.
