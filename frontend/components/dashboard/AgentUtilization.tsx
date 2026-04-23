"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { AGENT_COLORS, AGENT_ORDER, type AgentName } from "@/lib/types";
import type { DashboardMetrics } from "@/lib/types";

export function AgentUtilization({ metrics }: { metrics: DashboardMetrics | null }) {
  const byAgent = new Map<string, { calls: number; avg_latency_ms: number }>(
    (metrics?.agent_stats ?? []).map((a) => [a.agent, a]),
  );
  return (
    <Card>
      <CardHeader>
        <CardTitle>Agent utilization</CardTitle>
        <CardDescription>
          Call count and average latency per agent (populated by the trace store).
        </CardDescription>
      </CardHeader>
      <CardContent>
        <ul className="space-y-2">
          {AGENT_ORDER.map((name: AgentName) => {
            const stat = byAgent.get(name) ?? { calls: 0, avg_latency_ms: 0 };
            return (
              <li key={name} className="flex items-center gap-3 text-sm">
                <span className={`h-2 w-2 rounded-full ${AGENT_COLORS[name]}`} />
                <span className="w-28 capitalize">{name}</span>
                <span className="tabular-nums text-xs text-muted-foreground w-16">
                  {stat.calls} call{stat.calls === 1 ? "" : "s"}
                </span>
                <span className="tabular-nums text-xs text-muted-foreground">
                  {stat.avg_latency_ms ? `${stat.avg_latency_ms.toFixed(0)} ms avg` : "—"}
                </span>
              </li>
            );
          })}
        </ul>
      </CardContent>
    </Card>
  );
}
