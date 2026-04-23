"use client";

import { AlertOctagon, ListChecks, Sparkles } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import type { FinalReport } from "@/lib/types";

const SEVERITY_COLOR: Record<string, string> = {
  critical: "bg-rose-100 text-rose-800 dark:bg-rose-950 dark:text-rose-200",
  high: "bg-orange-100 text-orange-800 dark:bg-orange-950 dark:text-orange-200",
  medium: "bg-yellow-100 text-yellow-800 dark:bg-yellow-950 dark:text-yellow-200",
  low: "bg-blue-100 text-blue-800 dark:bg-blue-950 dark:text-blue-200",
};

export function ExecutiveBriefing({ report }: { report: FinalReport | null }) {
  if (!report) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Executive briefing</CardTitle>
          <CardDescription>
            Investigator will publish the plain-English briefing here once the scan completes.
          </CardDescription>
        </CardHeader>
      </Card>
    );
  }
  return (
    <Card>
      <CardHeader>
        <div className="flex items-center gap-2">
          <Sparkles className="h-5 w-5 text-amber-500" />
          <CardTitle>Executive briefing</CardTitle>
        </div>
        <CardDescription className="leading-relaxed">
          {report.executive_summary}
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        <section>
          <h4 className="text-xs uppercase tracking-wider font-semibold text-muted-foreground mb-2 flex items-center gap-1.5">
            <AlertOctagon className="h-3.5 w-3.5" />
            Critical findings
          </h4>
          <ol className="space-y-3">
            {report.critical_findings.map((f, idx) => (
              <li key={idx} className="rounded-md border px-3 py-2">
                <div className="flex items-start justify-between gap-2">
                  <span className="font-medium text-sm">{f.headline}</span>
                  <Badge className={SEVERITY_COLOR[f.severity] ?? "bg-muted"}>
                    {f.severity}
                  </Badge>
                </div>
                <p className="text-xs text-muted-foreground mt-1 leading-relaxed">
                  {f.detail}
                </p>
                {(f.linked_cves.length > 0 || f.linked_techniques.length > 0) && (
                  <div className="mt-2 flex flex-wrap gap-1">
                    {f.linked_cves.map((c) => (
                      <span key={c} className="text-[10px] rounded bg-muted px-1.5 py-0.5 font-mono">
                        {c}
                      </span>
                    ))}
                    {f.linked_techniques.map((t) => (
                      <span
                        key={t}
                        className="text-[10px] rounded border px-1.5 py-0.5 font-mono"
                      >
                        {t}
                      </span>
                    ))}
                  </div>
                )}
              </li>
            ))}
          </ol>
        </section>

        <section>
          <h4 className="text-xs uppercase tracking-wider font-semibold text-muted-foreground mb-2 flex items-center gap-1.5">
            <ListChecks className="h-3.5 w-3.5" />
            Recommended actions
          </h4>
          <ol className="space-y-2">
            {report.recommended_actions.map((a, idx) => (
              <li
                key={idx}
                className="flex items-center justify-between rounded-md border px-3 py-2"
              >
                <div className="flex items-center gap-3">
                  <span className="text-sm font-semibold text-muted-foreground w-6">
                    #{a.priority}
                  </span>
                  <span className="text-sm">{a.description}</span>
                </div>
                <div className="flex items-center gap-2 text-xs">
                  <span className="text-muted-foreground">{a.estimated_effort}</span>
                  <Badge variant="outline" className="font-normal">
                    {a.owner_suggestion.replace(/_/g, " ")}
                  </Badge>
                </div>
              </li>
            ))}
          </ol>
        </section>

        <section>
          <h4 className="text-xs uppercase tracking-wider font-semibold text-muted-foreground mb-2">
            What PrePulse would do
          </h4>
          <p className="text-sm leading-relaxed text-muted-foreground">
            {report.what_prepulse_would_do}
          </p>
        </section>
      </CardContent>
    </Card>
  );
}
