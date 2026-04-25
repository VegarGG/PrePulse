# FAQ

### Is any of this real?

The reasoning is real — same Claude Sonnet 4.6 model that would power
production PrePulse. The retrieval against MITRE ATT&CK is real (835
techniques loaded into a vector store at startup). The threat-intel APIs
(OTX, HIBP, AbuseIPDB, NVD) are real and live mode is one environment
flag away (`PREPULSE_LIVE=1`). What is simulated in the prototype is the
*execution* of defensive actions against real infrastructure — every
would-be mutation is logged and narrated, which is what lets us
demonstrate a six-agent fleet safely in an academic context.

### How is this different from a GenAI copilot bolted onto Splunk?

A copilot reacts to alerts a legacy SIEM already generates. PrePulse's
fleet plans, validates, and acts without waiting for the SIEM to trigger.
The Hardening agent rotates attack surface before an attack lands, the
Validator confirms exploitability before remediation is prioritised, and
the Supervisor cross-checks the fleet's own reasoning. Different layer of
the stack, different value proposition.

### Why an agent fleet and not one big agent?

Two reasons — observability and policy. With six agents each responsible
for a narrow function, a reviewer can watch the system reason in real
time, and the Supervisor can cross-check any one agent's output against
the others. A single monolithic agent would be faster to build but
impossible to govern under compliance regimes like the EU AI Act.

### What is the posture score?

A deterministic 0–100 score the Investigator publishes after the
Validator and Hardening agents finish. Computed in Python (not by the
LLM): starts at 100, deducts for CVEs by severity (10/5/3/1 per
critical/high/medium/low), deducts 15 for a breached domain, deducts 10
when active campaigns ≥ 3, deducts 8 per high-confidence abuse IP, adds 5
for a clean intel posture, and adds 2 per hardening action taken. Clamped
to [0, 100]. Grade bands: A ≥ 90, B ≥ 75, C ≥ 60, D ≥ 40, F < 40.

### What happens if I dismiss the approval modal?

It counts as a **reject**. The orchestrator's awaited future resolves
with `approved=False`, the action is marked rejected, and the scan
continues to the Supervisor. Dismissal can never silently leave the gate
hanging.

### Can I run it offline?

Yes — set `PREPULSE_LIVE=0` (the default). Threat-intel API calls are
served from per-profile fixtures in `backend/demo/mocks/`. The MITRE
vector store also has an offline fallback using deterministic fake
embeddings. The only outbound call that genuinely needs internet is the
Anthropic API for the agent reasoning itself.

### What's in the dashboard?

KPIs (total scans, threats detected, actions executed, average posture
score, mean-time-to-contain), a 30-day posture trend, severity
distribution across CVEs, defense actions by kind, top MITRE techniques
ranked by hit count, and per-agent utilisation. On first boot the store
is seeded with 30 days of deterministic synthetic history (≈120 scans)
so the dashboard is never empty.

### Where do I add more knowledge for the chatbot?

Drop a Markdown file into `backend/knowledge_base/`. The chatbot loads
every `.md` in that folder at server startup (`README.md` is excluded).
Restart the backend to pick up new content.
