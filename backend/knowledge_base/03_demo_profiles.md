# Demo Profiles

The prototype ships with three scripted company profiles. Each one drives a
different narrative arc through the agent fleet. Mock data for each profile
lives under `backend/demo/mocks/<profile_id>/`.

## River City Financial Services (`river_city`)
- **Industry:** fintech · **Employees:** 87 · **Domain:** rivercity.fin
- **Tech stack:** AWS Lambda, PostgreSQL, Stripe, GitHub Enterprise, Slack
- **Expected posture score:** 48 (Grade D — elevated risk)
- **Narrative:** Regional fintech with a breached domain (LinkedIn 2021 +
  Collection #1 dumps), an exploitable Lambda CVE
  (CVE-2026-10234, CVSS 9.8, public PoC), and an active Grandoreiro
  banking-trojan campaign targeting the industry. Demonstrates the **full
  remediation arc**: Hardening rotates the MTD port map, Remediator
  proposes blocking the malicious IP and forcing MFA, the human-in-the-loop
  modal fires, and Supervisor signs off.

## Greenfield Family Clinic (`greenfield`)
- **Industry:** healthcare · **Employees:** 42 · **Domain:** greenfieldclinic.health
- **Tech stack:** Microsoft Exchange 2019, Windows Server 2019, Veeam
  Backup, Meditech EHR, Outlook
- **Expected posture score:** 32 (Grade F — critical)
- **Narrative:** Small clinic with an unpatched Exchange 2019 server, the
  active BlackBasta ransomware campaign targeting healthcare, and a
  high-confidence abuse IP probing the network. Demonstrates **escalation**
  to human review and the most aggressive containment plan.

## ShopLocal Marketplace (`shoplocal`)
- **Industry:** e-commerce · **Employees:** 120 · **Domain:** shoplocal.market
- **Tech stack:** Shopify, Cloudflare, MySQL, Stripe, Twilio
- **Expected posture score:** 72 (Grade C — healthy)
- **Narrative:** Mid-market e-commerce marketplace with no breaches, only
  minor CVEs, and a low active-threat count. Demonstrates the **clean-scan
  happy path** — Remediator may still trigger because posture is below 75,
  but the action set is small.

## Custom profiles

The landing page also exposes a free-form profile form. Any
prompt-injection attempts in the company name, domain, or tech stack are
caught by the InputValidator and rejected with HTTP 400 before reaching
any LLM.
