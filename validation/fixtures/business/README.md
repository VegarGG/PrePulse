# Week 4 — Business Validation Protocol

Per validation plan §8 (Week 4): 10–15 customer-discovery interviews
with SMB owners or IT managers, plus competitor benchmarking. Pilot
the prototype demo with a subset.

Not automated. The pipeline emits one `inconclusive` row for this
campaign; the actual interviews are conducted by hand.

## Interview structure (45 min)

### Block 1 — Pain-point discovery (15 min)
Goal: validate that the pain PrePulse claims to solve is real for this
participant *without* leading them with PrePulse-specific framing.

Open: "Walk me through how you currently handle cybersecurity at your
organisation — who does it, what tools, how do you decide if you're
covered?"

Probes: incident history; near-miss anecdotes; budget; perceived gaps;
who they would call at 2am if compromised.

Capture: **does the participant volunteer a pain point that PrePulse
addresses, unprompted?** (yes / partial / no)

### Block 2 — Current solutions (10 min)
Goal: enumerate the existing alternatives. Pricing, satisfaction,
switching cost.

Probes: current MDR/EDR/SIEM; staffing; outsourced SOC; cyber
insurance requirements; compliance obligations.

Capture: list of named competitors + per-competitor satisfaction (1–5).

### Block 3 — Prototype demo (10 min)
Drive the 5-minute demo script (river_city → scan → approval → posture
+ briefing → dashboard). Let them ask questions.

Capture: emotional reaction (genuine interest / polite / sceptical /
hostile); top 2 questions they ask; whether they ask "how much?".

### Block 4 — Willingness to pay (10 min)
Use the **Van Westendorp Price-Sensitivity Meter** (4 questions, anchored
on monthly subscription per organisation):

- "At what price would you consider this product *too expensive* to
  consider?"
- "At what price would you consider it *expensive but you might still
  buy*?"
- "At what price would it be a *bargain* — a great buy?"
- "At what price would it be *so cheap* you'd question its quality?"

Capture: four numbers per participant. The intersection of demand
curves yields the indifference price (IPP) and optimum price (OPP).

## Quantitative deliverables (per the plan)

- Pain-point validation rate: % of participants who recognised the
  pain unprompted (Block 1).
- Willingness-to-pay distribution: histogram of OPP across N
  participants.
- Competitor list with satisfaction scores.
- Free-text findings categorised as critical / high / medium / low.

## Recording

- Audio recordings (with consent): `validation/runs/<campaign>/business/<id>.m4a`
- Per-interview JSONL row: `validation/runs/<campaign>/business/interviews.jsonl`
- VW responses CSV: `validation/runs/<campaign>/business/vw_pricing.csv`
- Competitor matrix: `validation/runs/<campaign>/business/competitors.csv`

## Synthesis output

`validation/reports/<campaign>_business_report.md` — pain-point
validation rate (with Wilson 95% CI), Van Westendorp curves, competitor
matrix, top 5 surprises.
