"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import type { DashboardMetrics } from "@/lib/types";

const SEV_ORDER: Array<keyof NonNullable<DashboardMetrics>["series"]["severities_30d"]> = [
  "CRITICAL",
  "HIGH",
  "MEDIUM",
  "LOW",
  "INFO",
];

const SEV_COLOR: Record<string, string> = {
  CRITICAL: "hsl(0, 72%, 51%)",
  HIGH: "hsl(22, 89%, 55%)",
  MEDIUM: "hsl(42, 89%, 54%)",
  LOW: "hsl(210, 72%, 54%)",
  INFO: "hsl(0, 0%, 60%)",
};

export function ThreatsBySeverity({ metrics }: { metrics: DashboardMetrics | null }) {
  const byLevel = metrics?.series.severities_30d ?? {};
  const data = SEV_ORDER.map((sev) => ({
    severity: sev,
    count: byLevel[sev] ?? 0,
    fill: SEV_COLOR[sev],
  }));
  const total = data.reduce((s, d) => s + d.count, 0);

  return (
    <Card>
      <CardHeader>
        <CardTitle>Threats by severity</CardTitle>
        <CardDescription>
          Distribution across all validated CVEs surfaced in this session.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="h-64">
          {total === 0 ? (
            <div className="h-full flex items-center justify-center text-sm text-muted-foreground">
              No CVEs validated yet.
            </div>
          ) : (
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={data}>
                <CartesianGrid strokeDasharray="3 3" strokeOpacity={0.3} />
                <XAxis dataKey="severity" tick={{ fontSize: 11 }} />
                <YAxis allowDecimals={false} tick={{ fontSize: 11 }} />
                <Tooltip
                  contentStyle={{
                    borderRadius: 8,
                    fontSize: 12,
                    background: "hsl(var(--popover))",
                    color: "hsl(var(--popover-foreground))",
                  }}
                />
                <Bar dataKey="count" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
