

**PrePulse \-** 

**Preemptive, Agentic Security**

*A GenAI-native preemptive defense platform delivered as an outcome to small and mid-market organizations*

 

Prepared by: Ziwei Huang (zh1459@nyu.edu)

Course: Beyond Data – GenAI-Driven Business Strategy & Reinvention

NYU Tandon School of Engineering

Instructor: Marco Magnini ([marco.magnini@nyu.edu](mailto:marco.magnini@nyu.edu))

Date: Apr 13, 2026

# **Executive Summary**

PrePulse is a preemptive, agentic-AI security platform delivered as a measurable outcome to small and mid-market organizations. It combines Gartner’s four pillars of preemptive cybersecurity — predictive threat intelligence, adversarial exposure validation, automated moving target defense, and autonomous agentic security operations — into a single cloud-native service that is priced on incidents averted rather than licenses consumed. PrePulse targets two customer segments identified in the Task 1 analysis: Segment C (small and medium businesses) and Segment B (mid-market digital natives). The platform’s central differentiator is an orchestrated fleet of specialized AI agents that collectively act as an autonomous cyber-immune system, compressing what traditional managed detection and response providers deliver with teams of fifty analysts into a software service that a ten-person company can afford. The proposal below outlines the concept, value proposition, architectural components, business model, and principal execution risks.

# **1\. Product Name and Description**

Product name: PrePulse. The name conveys the platform’s core thesis — sensing the pulse of adversary activity ahead of detonation — and signals that prevention, not response, is the unit of value. PrePulse is deployed as a SaaS control plane with lightweight telemetry collectors across the customer’s endpoints, identities, cloud accounts, and email tenant. Once onboarded, the platform continuously ingests external predictive threat intelligence, validates the exploitability of exposures through automated adversarial emulation, hardens endpoints through automated moving target defense, and operates an autonomous agentic security operations center that investigates, contains, and remediates incidents on the customer’s behalf.

Unlike traditional managed security service providers that deliver alerts and expect customers to act, PrePulse delivers outcomes. The platform produces a continuously updated preemptive security posture score, a short list of exploitable exposures with automated remediation playbooks, and a monthly attestation of incidents averted. When the platform cannot contain an incident autonomously, a human overseer from PrePulse’s managed-service tier intervenes, with the customer paying an escalation fee rather than a baseline retainer.

# **2\. Intended Target Market Segment**

PrePulse is purpose-built for the two most under-served segments in the Task 1 analysis. Segment C — small and medium businesses with fewer than 500 employees and no dedicated security staff — is the fastest-growing ransomware-victim pool because attackers correctly perceive it as poorly defended and economically rational to target at scale. Existing solutions for this segment bundle a single endpoint product with cyber insurance, leaving material detection-and-response gaps that commodity attacker tooling routinely exploits. Segment B — mid-market digital natives in software, fintech, media, and direct-to-consumer retail — runs cloud-first with lean security teams of five to thirty engineers. Heavyweight agent-based platforms conflict with their ephemeral, containerized workloads, and preemptive tooling has historically been architected around enterprise-grade SOC teams rather than small DevSecOps units.

PrePulse addresses both segments with a single architecture and two commercial packages. The SMB package emphasizes managed outcomes, channel delivery, and bundled cyber-insurance alignment. The mid-market package emphasizes API-first integration with continuous-integration pipelines, infrastructure-as-code, and cloud-native identity providers. Both packages share the same underlying agent fleet, reducing engineering fragmentation and allowing learnings from one customer base to improve defenses for the other.

# **3\. Unique Value Proposition**

PrePulse’s value proposition rests on three claims that differentiate it from both incumbent managed detection-and-response providers and first-generation GenAI copilots. Each claim is tied directly to an unmet need surfaced in Task 1\.

## **3.1 Outcome-Priced Preemption, Not Alert Volume**

Traditional managed security services charge per endpoint or per gigabyte of telemetry, which creates a perverse incentive to maximize coverage even when coverage does not translate to risk reduction. PrePulse prices on a hybrid model: a modest platform fee plus an outcome component keyed to incidents averted, mean-time-to-contain, and exposure reduction. Premiums are tied to attestations that insurance carriers can underwrite against, converting cybersecurity spend into a measurable risk-transfer mechanism. This directly addresses the SMB frustration that today’s solutions generate alerts without delivering remediation.

## **3.2 An Agent Fleet, Not a Single Copilot**

Most GenAI security products to date are single copilots bolted onto a legacy SOC workflow. PrePulse is architected as a coordinated fleet of specialized agents, each with a narrow mandate and independently testable behavior. The Intelligence agent ingests predictive threat feeds and tailors them to the customer’s industry, geography, and infrastructure. The Validator agent runs continuous adversarial exposure validation campaigns against the live environment to confirm which exposures are actually exploitable. The Hardening agent orchestrates automated moving target defense and identity posture changes. The Investigator agent triages incidents by chaining evidence across endpoints, identities, email, and cloud. The Remediator agent executes containment playbooks, subject to guardrails and human approval thresholds the customer configures. A Supervisor agent audits the others, enforces policy, and escalates to human overseers when confidence drops below a configurable threshold.

## **3.3 Transparent AI Assurance by Default**

Segment A-grade assurance is increasingly demanded by Segment B and Segment C buyers as their customers and regulators look through to their supply chains. PrePulse ships with a built-in AI assurance module that exposes the reasoning trace of every agent decision, records the data provenance of every model prompt and response, and certifies guardrails against prompt injection from adversarial content in ingested telemetry. This transparency is a sales asset in regulated verticals such as healthcare SMBs and fintech scale-ups, and it is increasingly expected under emerging regimes such as the EU AI Act and the US SEC’s cyber disclosure rules.

# **4\. Product Architecture and Core GenAI Components**

The PrePulse platform is organized around five modules mapped explicitly to the preemptive cybersecurity taxonomy developed in Task 1, Section 3\. Table 1 summarizes the mapping.

| Module | Preemptive Pillar | GenAI Technique |
| :---- | :---- | :---- |
| **Intelligence** | Predictive Threat Intelligence | Domain-specific LLM fine-tuned on adversary infrastructure telemetry; vector retrieval over a curated threat corpus |
| **Validator** | Adversarial Exposure Validation | Agentic multi-step attack planner that chains techniques against a live shadow environment |
| **Hardening** | Automated Moving Target Defense | Reinforcement-learning policy that continuously mutates process layouts and identity posture within safe bounds |
| **Investigator** | Agentic SOC Copilot | Reasoning-optimized LLM with tool-use over SIEM, identity, email, and cloud APIs; multi-hop evidence chaining |
| **Remediator / Supervisor** | Autonomous Cyber-Immune Response | Policy-constrained agent with bounded autonomy, deterministic playbooks, and formal guardrail verification |

*Table 1\. Mapping of PrePulse modules to the preemptive cybersecurity taxonomy.*

Two architectural choices deserve particular attention. First, PrePulse uses a mixture of small domain-specific language models and larger general-purpose reasoning models, routing each subtask to the smallest model that can complete it with acceptable confidence. This keeps inference costs manageable at SMB price points and reduces the blast radius of any single model failure. Second, the platform treats adversarial robustness as a first-class design concern: all prompts that contain ingested telemetry are sandwiched between tamper-detection wrappers, model outputs are cross-validated across independent agents before any action is taken, and the Supervisor agent applies deterministic policy checks before the Remediator is permitted to execute containment.

# **5\. Business Model and Pricing**

PrePulse uses a three-tier commercial model. The Essentials tier targets SMBs through managed-service-provider and cyber-insurance channel partners; it is priced at a low monthly platform fee with a pay-on-incident-averted rider. The Velocity tier targets mid-market digital natives through direct sales; it adds developer-native integrations with continuous-integration pipelines, infrastructure-as-code, and cloud identity providers. The Enterprise Assurance tier targets larger regulated buyers that need the same preemptive capability but with contract-grade AI assurance, sovereign deployment options, and custom compliance attestations. Across all tiers, pricing is designed to align vendor incentives with customer outcomes, reinforcing the platform’s core narrative of prevention as a service.

# 

# 

# 

# **6\. Preliminary Development Plan and Challenges**

A realistic twenty-four-month path to general availability proceeds in three phases. Phase one (months one to six) delivers the Intelligence and Investigator agents on top of a single well-understood telemetry source (identity logs), validates performance against publicly available red-team benchmarks, and secures a small design-partner cohort in the SMB segment. Phase two (months seven to fifteen) adds the Validator and Hardening agents, extends telemetry coverage to endpoint and email, and completes SOC 2 Type II and ISO 27001 audits. Phase three (months sixteen to twenty-four) adds the Supervisor and Remediator agents with progressively broader autonomy, concludes the first insurance-carrier partnership for outcome underwriting, and opens general availability for Segment B.

Four categories of risk dominate the execution profile. The first is agent trust: autonomous remediation in customer environments requires extremely high precision, because a false-positive containment action can be more damaging than the incident it was meant to prevent. PrePulse mitigates this through staged autonomy, deterministic policy guardrails, and observable reasoning traces. The second is adversarial prompt injection of ingested telemetry, where attackers deliberately plant content designed to manipulate the agents’ prompts; PrePulse mitigates this with tamper-detection wrappers, cross-agent verification, and independent red-team evaluations. The third is go-to-market economics, particularly the cost of customer acquisition at SMB price points; the channel strategy through managed-service providers and insurance carriers is designed to solve this. The fourth is regulatory evolution, as the EU AI Act, US SEC rules, and sectoral regulators continue to refine expectations for autonomous AI systems in security-critical functions; the Assurance module is designed to adapt to these regimes as they mature.

If PrePulse executes against this plan, it will occupy a defensible position at the intersection of two of the highest-growth vectors in the cybersecurity market: the shift to preemptive defense and the descent of enterprise-grade capability into the under-served SMB and mid-market segments. The product is grounded in the segmentation and trend analysis from Task 1, directly responsive to the unmet needs identified there, and differentiated from both traditional managed services and first-generation AI copilots by its agent-fleet architecture, outcome-based pricing, and built-in AI assurance.

# 

# 

# 

# 

# 

# **References**

**Gartner. (2025).** Preemptive cybersecurity solutions: A must in modern tech products. Gartner. https://www.gartner.com/en/articles/preemptive-cybersecurity-solutions

**Gartner. (2025, September 18).** Gartner says that in the age of GenAI, preemptive capabilities, not detection and response, are the future of cybersecurity \[Press release\]. https://www.gartner.com/en/newsroom/press-releases/2025-09-18-gartner-says-that-in-the-age-of-genai-preemptive-capabilities-not-detection-and-response-are-the-future-of-cybersecurity

**Gartner Peer Insights. (2026).** Best adversarial exposure validation reviews 2026\. https://www.gartner.com/reviews/market/adversarial-exposure-validation

**Help Net Security. (2025, September 23).** Gartner: Preemptive cybersecurity to dominate 50% of security spend by 2030\. https://www.helpnetsecurity.com/2025/09/23/preemptive-cybersecurity-solutions-shift/

**Hadrian. (2025).** Hadrian recognized as a sample vendor in Gartner Emerging Tech Impact Radar: Preemptive cybersecurity, 2025\. https://hadrian.io/blog/hadrian-is-a-sample-vendor-in-gartner-r-emerging-tech-impact-radar-tm-preemptive-cybersecurity-2025

**Pentera. (2025).** Adversarial exposure validation (AEV) glossary. https://pentera.io/glossary/adversarial-exposure-validation-aev-glossary/

**Cyber Strategy Institute. (2025).** Adversarial exposure validation (AEV): The definitive guide to 2025 trends, challenges, innovations, and 2026 projections in cybersecurity. https://cyberstrategyinstitute.com/adversarial-exposure-validation-aev-the-definitive-guide-to-2025-trends-challenges-innovations-and-2026-projections-in-cybersecurity/

**Morphisec. (2025).** AI-driven cyber espionage is here — why Gartner says preemptive cybersecurity must come next. https://www.morphisec.com/blog/ai-driven-cyber-espionage-is-here-why-gartner-says-preemptive-cybersecurity-must-come-next/

**Network World. (2025, October).** AI dominates Gartner’s top strategic technology trends for 2026\. https://www.networkworld.com/article/4076316/ai-dominates-gartners-top-strategic-technology-trends-for-2026.html

**IBM Security. (2024).** Cost of a data breach report 2024\. IBM Corporation. https://www.ibm.com/reports/data-breach