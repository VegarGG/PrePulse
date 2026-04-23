"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import type { MitreTechnique } from "@/lib/types";

const TACTIC_ORDER = [
  "Reconnaissance",
  "Resource Development",
  "Initial Access",
  "Execution",
  "Persistence",
  "Privilege Escalation",
  "Defense Evasion",
  "Credential Access",
  "Discovery",
  "Lateral Movement",
  "Collection",
  "Command And Control",
  "Exfiltration",
  "Impact",
];

export function TacticHeatmap({ techniques }: { techniques: MitreTechnique[] }) {
  const byTactic = new Map<string, MitreTechnique[]>();
  for (const t of techniques) {
    const key = t.tactic || "Unknown";
    const list = byTactic.get(key) ?? [];
    list.push(t);
    byTactic.set(key, list);
  }
  return (
    <Card>
      <CardHeader>
        <CardTitle>MITRE ATT&CK tactics observed</CardTitle>
        <CardDescription>
          {techniques.length === 0
            ? "Validator hasn't matched any techniques yet."
            : `${techniques.length} technique${
                techniques.length === 1 ? "" : "s"
              } mapped across ${byTactic.size} tactic${byTactic.size === 1 ? "" : "s"}.`}
        </CardDescription>
      </CardHeader>
      {techniques.length > 0 && (
        <CardContent className="pt-0">
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-2">
            {TACTIC_ORDER.filter((t) => byTactic.has(t)).map((tactic) => {
              const hits = byTactic.get(tactic) ?? [];
              const intensity = Math.min(1, hits.length / 3);
              return (
                <div
                  key={tactic}
                  className="rounded-md border px-2 py-2 text-xs"
                  style={{
                    backgroundColor: `hsl(0, 70%, ${95 - intensity * 35}%)`,
                  }}
                  title={hits.map((h) => `${h.technique_id} ${h.technique_name}`).join("\n")}
                >
                  <div className="font-medium text-[11px] uppercase tracking-wide text-foreground/80">
                    {tactic}
                  </div>
                  <div className="mt-1 flex flex-wrap gap-1">
                    {hits.slice(0, 4).map((h) => (
                      <span
                        key={h.technique_id}
                        className="font-mono text-[10px] bg-background/70 rounded px-1 py-0.5"
                      >
                        {h.technique_id}
                      </span>
                    ))}
                  </div>
                </div>
              );
            })}
          </div>
        </CardContent>
      )}
    </Card>
  );
}
