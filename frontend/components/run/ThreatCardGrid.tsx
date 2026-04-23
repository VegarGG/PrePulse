"use client";

import { ShieldAlert } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import type { ThreatCampaign } from "@/lib/types";

const LEVEL_COLORS: Record<number, string> = {
  1: "bg-muted text-muted-foreground",
  2: "bg-blue-100 text-blue-800 dark:bg-blue-950 dark:text-blue-200",
  3: "bg-yellow-100 text-yellow-800 dark:bg-yellow-950 dark:text-yellow-200",
  4: "bg-orange-100 text-orange-800 dark:bg-orange-950 dark:text-orange-200",
  5: "bg-rose-100 text-rose-800 dark:bg-rose-950 dark:text-rose-200",
};

export function ThreatCardGrid({ campaigns }: { campaigns: ThreatCampaign[] }) {
  if (campaigns.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Active campaigns</CardTitle>
          <CardDescription>
            Intelligence hasn&apos;t reported any active campaigns yet.
          </CardDescription>
        </CardHeader>
      </Card>
    );
  }
  return (
    <div className="space-y-3">
      <h3 className="text-sm font-semibold tracking-tight text-muted-foreground">
        Active campaigns ({campaigns.length})
      </h3>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        {campaigns.slice(0, 6).map((c) => (
          <Card key={c.pulse_id}>
            <CardHeader className="pb-2">
              <div className="flex items-start justify-between gap-2">
                <ShieldAlert className="h-5 w-5 text-muted-foreground" />
                <Badge className={`${LEVEL_COLORS[c.threat_level] ?? "bg-muted"}`}>
                  L{c.threat_level}
                </Badge>
              </div>
              <CardTitle className="text-sm leading-snug">{c.title}</CardTitle>
            </CardHeader>
            <CardContent className="text-xs text-muted-foreground space-y-2">
              <p className="line-clamp-3 leading-relaxed">{c.description}</p>
              <div className="flex flex-wrap gap-1">
                {c.tags.slice(0, 4).map((t) => (
                  <span
                    key={t}
                    className="text-[10px] rounded bg-muted px-1.5 py-0.5 font-mono"
                  >
                    {t}
                  </span>
                ))}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
