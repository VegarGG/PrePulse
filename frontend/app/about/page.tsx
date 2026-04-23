import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export default function AboutPage() {
  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-semibold tracking-tight">About PrePulse</h1>
        <p className="text-sm text-muted-foreground max-w-3xl">
          Prototype deliverable for MG-9781 (NYU Tandon) — a preemptive, agentic-AI
          cybersecurity platform targeting small and mid-market organizations.
        </p>
      </header>

      <Card>
        <CardHeader>
          <CardTitle>Product vision</CardTitle>
          <CardDescription>
            A fleet of six specialized agents that plan, validate, and act, rather than a
            single copilot bolted onto a legacy SOC.
          </CardDescription>
        </CardHeader>
        <CardContent className="text-sm text-muted-foreground space-y-3 leading-relaxed">
          <p>
            The full-product vision bundles four pillars — predictive threat intelligence,
            adversarial exposure validation, automated moving target defense, and autonomous
            agentic security operations — into a single cloud-native service. Each agent
            reasons observably through traced decision chains, and staged autonomy ensures a
            human approval threshold sits in front of any potentially destructive action.
          </p>
          <p>
            In this prototype three agents (<strong>Intelligence</strong>,{" "}
            <strong>Validator</strong>, <strong>Investigator</strong>) perform real LLM
            reasoning over real or mocked threat-intelligence data. The three action-taking
            agents (<strong>Hardening</strong>, <strong>Remediator</strong>,{" "}
            <strong>Supervisor</strong>) simulate the act of taking defensive action — the
            tool calls are logged and narrated, but nothing mutates real infrastructure.
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Team</CardTitle>
          <CardDescription>NYU Tandon — MG-9781 · Spring 2026</CardDescription>
        </CardHeader>
        <CardContent className="text-sm">
          Ziwei Huang · Yunlong Chai · Xuanwei Fan · Zonghui Wu
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Acknowledgements</CardTitle>
        </CardHeader>
        <CardContent className="text-sm text-muted-foreground leading-relaxed">
          Threat intelligence feeds: AlienVault OTX, HaveIBeenPwned, AbuseIPDB, and the NIST
          National Vulnerability Database. Adversary taxonomy courtesy of MITRE ATT&amp;CK
          (used under the MITRE ATT&amp;CK Terms of Use — attribution required).
        </CardContent>
      </Card>
    </div>
  );
}
