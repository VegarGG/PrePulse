"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import type { DashboardMetrics } from "@/lib/types";

export function TopTacticsRanked({ metrics }: { metrics: DashboardMetrics | null }) {
  const list = metrics?.top_tactics ?? [];
  const max = list.length ? list[0].count : 1;

  return (
    <Card>
      <CardHeader>
        <CardTitle>Top MITRE techniques</CardTitle>
        <CardDescription>
          Most-matched techniques across all scans; hit count in orange.
        </CardDescription>
      </CardHeader>
      <CardContent>
        {list.length === 0 ? (
          <div className="h-40 flex items-center justify-center text-sm text-muted-foreground">
            No techniques mapped yet.
          </div>
        ) : (
          <ol className="space-y-2">
            {list.slice(0, 10).map((t) => (
              <li key={t.technique_id} className="flex items-center gap-3 text-sm">
                <span className="font-mono w-16 text-xs">{t.technique_id}</span>
                <div className="flex-1 truncate">{t.technique_name}</div>
                <div className="w-40 h-2 rounded bg-muted overflow-hidden">
                  <div
                    className="h-full bg-orange-500"
                    style={{ width: `${(t.count / max) * 100}%` }}
                  />
                </div>
                <span className="w-8 text-right tabular-nums text-xs text-muted-foreground">
                  {t.count}
                </span>
              </li>
            ))}
          </ol>
        )}
      </CardContent>
    </Card>
  );
}
