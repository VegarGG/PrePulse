"use client";

import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import type { DashboardMetrics } from "@/lib/types";

export function PostureTrendChart({ metrics }: { metrics: DashboardMetrics | null }) {
  const data =
    metrics?.series.posture_30d.map((p, idx) => ({
      idx,
      ts: new Date(p.ts).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      score: p.posture_score ?? null,
    })) ?? [];

  return (
    <Card>
      <CardHeader>
        <CardTitle>Posture trend</CardTitle>
        <CardDescription>
          Each point is one scan; the Y axis is the deterministic posture score (0-100).
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="h-64">
          {data.length === 0 ? (
            <EmptyState label="No scans recorded yet — run a scan to populate this chart." />
          ) : (
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={data}>
                <CartesianGrid strokeDasharray="3 3" strokeOpacity={0.3} />
                <XAxis dataKey="ts" tick={{ fontSize: 11 }} />
                <YAxis domain={[0, 100]} tick={{ fontSize: 11 }} />
                <Tooltip
                  contentStyle={{
                    borderRadius: 8,
                    fontSize: 12,
                    background: "hsl(var(--popover))",
                    color: "hsl(var(--popover-foreground))",
                  }}
                />
                <Line
                  type="monotone"
                  dataKey="score"
                  stroke="hsl(var(--chart-2))"
                  strokeWidth={2}
                  dot={{ r: 3 }}
                  activeDot={{ r: 5 }}
                />
              </LineChart>
            </ResponsiveContainer>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

function EmptyState({ label }: { label: string }) {
  return (
    <div className="h-full flex items-center justify-center text-sm text-muted-foreground">
      {label}
    </div>
  );
}
