# The Six-Agent Fleet

PrePulse is built around six specialized agents that coordinate through a
LangGraph state machine. Three agents perform real LLM reasoning over real
or mocked threat-intelligence data; the three action-taking agents
(Hardening, Remediator, Supervisor) simulate defensive actions in this
prototype — the tool calls are logged and narrated, but nothing mutates
real infrastructure.

## 1. Intelligence
Reads from: company profile.
Writes: `IntelligenceReport`.
Question it answers: *"What is happening in the wild that matters to this
company?"* It pulls active threat campaigns matching the industry, checks
the domain against breach corpora, and probes a handful of suspicious IPs.
Tools available: `otx.get_pulses`, `hibp.check_domain`,
`abuseipdb.check_ip`.

## 2. Validator
Reads from: `intel_report` + tech stack.
Writes: `ValidationReport`.
Question: *"Are we actually vulnerable to any of it?"* Queries NVD for CVEs
affecting the declared stack and retrieves the most semantically relevant
MITRE ATT&CK techniques. Tools: `nvd.query_cves`,
`mitre.match_techniques`.

## 3. Hardening
Reads from: `intel_report` (and `validation_report` when available).
Writes: `HardeningReport`.
Question: *"What preemptive moves make us a harder target?"* Decides on
moving-target-defense actions — port-map rotation, certificate refresh,
attack-surface reduction — based on threats and validated exposures. All
actions are simulated. Tools: `mtd.rotate_port_map`, `mtd.refresh_certs`,
`iam.rotate_credentials`. Validator and Hardening run **in parallel**
after Intelligence completes.

## 4. Investigator
Reads from: all prior reports.
Writes: `FinalReport`.
Question: *"Putting it all together, what is going on and how bad is it?"*
Synthesizes prior agent outputs, computes the deterministic posture score
(0–100), and writes the executive briefing in plain English for a
non-technical reader. The deterministic engine is authoritative — the LLM
cannot drift from the computed score.

## 5. Remediator
Reads from: `final_report` + `hardening_report`.
Writes: `RemediationReport`.
Question: *"Given the briefing, what are we going to do about it?"* Builds
a prioritized containment plan of 2–5 actions. Destructive actions
(severity `high` or `critical`) are gated behind a **human approval**
modal in the UI before execution. Approved tools: `firewall.block_ip`,
`firewall.block_range`, `iam.force_mfa`, `iam.rotate_credentials`,
`iam.disable_user`, `endpoint.isolate`, `endpoint.quarantine_file`,
`ticketing.open_incident`, `email.notify_admin`.

## 6. Supervisor
Reads from: all prior reports.
Writes: `SupervisorReport`.
Question: *"Are the other agents being sensible?"* Reviews the agent
trace, cross-checks for hallucinations and low-confidence findings, and
either signs off, applies a conditional approval, or escalates to human
review. Tools: `policy.check`, `audit.log_decision`.

## Orchestration topology

```
intelligence ──► validator ─┐
              └► hardening ─┴► investigator ─┬─ posture < 75 ─► remediator ─► supervisor ─► END
                                             └─ posture ≥ 75 ─────────────► supervisor ─► END
```

A scan emits live SSE events for every lifecycle transition and every
tool call, so the run console renders the agents' reasoning in real time.
