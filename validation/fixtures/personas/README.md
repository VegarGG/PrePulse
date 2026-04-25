# Week 3 — User Testing Protocol

Per validation plan §8 (Week 3): recruit 6–8 participants matching the
three personas below. For each participant: 30-minute think-aloud
session, screen-recorded, followed by a 10-question System Usability
Scale (SUS) questionnaire.

This module is **not automated**. The pipeline records an `inconclusive`
row pointing here so the master report still references the campaign.

## Personas

### Persona A — SMB owner (non-technical)
Profile: founder of a 30-person professional-services firm. Reads tech
news; cannot explain TLS. Buys SaaS based on outcomes ("does it stop
ransomware?") not features. Decides without IT input.

Hostility: medium — sceptical of AI claims; wants to understand what
the product *does* before trusting it.

### Persona B — Office IT manager
Profile: solo IT generalist at an 80-person company. Manages M365,
laptops, network, vendor reviews. Has heard of MITRE ATT&CK; cannot
recite a technique ID. Evaluates security tools as part of his job.

Hostility: low — wants better tools; sceptical of ones that promise
magic.

### Persona C — Security analyst (evaluator)
Profile: junior analyst at an MSSP; tasked with shortlisting tools for
SMB clients. Has used CrowdStrike, Defender, Splunk. Reads
architecture docs.

Hostility: high — has seen many "AI security" pitches that under-
deliver. Will probe edges.

## Tasks (5)

1. **Open the dashboard, identify the most-recent low-posture scan.**
   Pass criterion: participant points to the correct row within 60s.

2. **Trigger a scan against the Greenfield demo profile.**
   Pass criterion: scan launched, run console reached, without help.

3. **During the scan, locate and approve the human-in-the-loop action.**
   Pass criterion: modal noticed, approval given, scan continues.

4. **Open the trace download for any completed scan and describe what
   it contains in your own words.**
   Pass criterion: participant identifies the trace as an audit log,
   downloadable artifact.

5. **Ask the chatbot one question you would actually want answered as
   a buyer.** Pass criterion: question is on-topic for the product;
   participant reports the answer was satisfactory.

## Per-task capture

For each task, log:
- `participant_id`, `persona` (A/B/C)
- `started_at`, `completed_at`, `time_to_complete_s`
- `result` ∈ {pass, fail_with_help, fail_abandon}
- `errors_observed` (count of false starts, dead ends)
- `verbatim_quote` (one notable utterance)

## SUS

After all five tasks, administer the standard 10-question SUS instrument
(usability.gov). Score 0–100; >68 = above average; >80 = excellent.

## Recording

- Screen recordings: `validation/runs/<campaign>/personas/<participant_id>.mp4`
- Per-task JSONL: `validation/runs/<campaign>/personas/sessions.jsonl`
- SUS scores: `validation/runs/<campaign>/personas/sus.csv`

## Synthesis output

`validation/reports/<campaign>_ux_report.md` — per task: completion
rate, mean time, themes from think-aloud commentary, SUS distribution.
