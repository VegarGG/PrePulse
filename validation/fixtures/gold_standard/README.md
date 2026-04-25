# Gold-standard scenario set (F-06, F-11, F-33)

Per the validation plan §6.2: 15 expert-authored scenarios, each pairing a
`CompanyProfile` input with an "expected" output across all six agents.
Used to compute gold-standard agreement (target ≥ 80%) and to validate
the deterministic posture engine.

Each scenario is a JSON file matching the `scenario_template.json`
schema. Two example scenarios are checked in to anchor the format
(`example_*.json`); a security-literate team member should author the
remaining 13 over ~2 person-days.

## Required fields per scenario

```jsonc
{
  "scenario_id": "fintech_breached_lambda",      // unique
  "narrative": "Regional fintech, breached domain, exploitable Lambda CVE",
  "profile": { /* CompanyProfile */ },
  "expected": {
    "intelligence": {
      "min_active_campaigns": 2,
      "domain_breached": true,
      "must_cite_pulses": ["banking-trojan"]    // tags or substrings
    },
    "validator": {
      "must_cite_cves": ["CVE-2026-10234"],
      "must_cite_techniques": ["T1190"],
      "min_exploitable_count": 1
    },
    "hardening": {
      "min_actions": 1,
      "preferred_kinds": ["mtd_port_rotation", "iam_rotate_credentials"]
    },
    "investigator": {
      "expected_posture_score": 48,             // ±2 tolerance
      "expected_grade": "D",
      "must_link_cves": ["CVE-2026-10234"],
      "must_link_techniques": ["T1190"]
    },
    "remediator": {
      "must_propose_kinds": ["firewall.block_ip", "iam.force_mfa"],
      "max_actions": 5
    },
    "supervisor": {
      "expected_sign_off": ["approved", "conditional"]   // either acceptable
    }
  }
}
```

## Author guidelines

- Author each scenario with two reviewers (one author, one peer review).
- Prefer concrete CVE/technique IDs; if you must use "any high-severity
  Lambda CVE", note that explicitly.
- Score the expected posture by hand using `compute_posture_score()`
  with reasonable assumed inputs; do not let the LLM author this number.
- File paths: `validation/fixtures/gold_standard/<scenario_id>.json`.
