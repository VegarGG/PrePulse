"use client";

import { Activity, Gauge, ShieldAlert, Timer, Wrench } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import type { DashboardMetrics } from "@/lib/types";

function fmtSeconds(s: number): string {
  if (!s) return "—";
  if (s < 60) return `${Math.round(s)}s`;
  if (s < 3600) return `${Math.round(s / 60)}m`;
  return `${(s / 3600).toFixed(1)}h`;
}

export function KpiStrip({ metrics }: { metrics: DashboardMetrics | null }) {
  const r = metrics?.rolling;
  const items = [
    {
      title: "Total scans",
      value: r?.total_scans ?? 0,
      Icon: Activity,
      description: "Scans stored in this session",
    },
    {
      title: "Threats detected",
      value: r?.threats_detected ?? 0,
      Icon: ShieldAlert,
      description: "Campaigns + CVEs surfaced",
    },
    {
      title: "Actions executed",
      value: r?.actions_executed ?? 0,
      Icon: Wrench,
      description: "Simulated defensive actions",
    },
    {
      title: "Avg posture",
      value: r ? `${r.avg_posture_score.toFixed(1)}` : "—",
      Icon: Gauge,
      description: "Deterministic engine, 0-100",
    },
    {
      title: "MTTC",
      value: fmtSeconds(r?.mean_time_to_contain_s ?? 0),
      Icon: Timer,
      description: "Mean time to contain",
    },
  ];

  return (
    <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
      {items.map(({ title, value, Icon, description }) => (
        <Card key={title}>
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <CardDescription className="text-xs">{title}</CardDescription>
              <Icon className="h-4 w-4 text-muted-foreground" />
            </div>
            <CardTitle className="text-2xl tabular-nums">{value}</CardTitle>
          </CardHeader>
          <CardContent className="pt-0 pb-4 text-[10px] text-muted-foreground">
            {description}
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
