"use client";

import { useEffect, useState } from "react";
import { getMetrics } from "@/lib/api";
import type { DashboardMetrics } from "@/lib/types";
import { KpiStrip } from "@/components/dashboard/KpiStrip";
import { PostureTrendChart } from "@/components/dashboard/PostureTrendChart";
import { ThreatsBySeverity } from "@/components/dashboard/ThreatsBySeverity";
import { ActionsByKind } from "@/components/dashboard/ActionsByKind";
import { TopTacticsRanked } from "@/components/dashboard/TopTacticsRanked";
import { AgentUtilization } from "@/components/dashboard/AgentUtilization";

export default function DashboardPage() {
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null);

  useEffect(() => {
    const load = () => getMetrics().then(setMetrics).catch(() => {});
    load();
    const id = setInterval(load, 10_000);
    return () => clearInterval(id);
  }, []);

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-semibold tracking-tight">Dashboard</h1>
        <p className="text-sm text-muted-foreground">
          Rolling KPIs and trends across every scan in this session. Auto-refreshes every 10s.
        </p>
      </header>

      <KpiStrip metrics={metrics} />

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <PostureTrendChart metrics={metrics} />
        <ThreatsBySeverity metrics={metrics} />
        <ActionsByKind metrics={metrics} />
        <TopTacticsRanked metrics={metrics} />
      </div>

      <AgentUtilization metrics={metrics} />
    </div>
  );
}
