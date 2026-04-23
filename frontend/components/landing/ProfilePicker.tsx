"use client";

import { Building2, HeartPulse, ShoppingBag, ArrowRight } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import type { DemoProfileSummary } from "@/lib/types";

const ICONS: Record<string, React.ComponentType<{ className?: string }>> = {
  fintech: Building2,
  healthcare: HeartPulse,
  "e-commerce": ShoppingBag,
};

function scoreColor(score: number): string {
  if (score >= 75) return "text-emerald-600 dark:text-emerald-400";
  if (score >= 60) return "text-yellow-600 dark:text-yellow-400";
  if (score >= 40) return "text-orange-600 dark:text-orange-400";
  return "text-rose-600 dark:text-rose-400";
}

export function ProfilePicker({
  profiles,
  onSelect,
  loadingId,
}: {
  profiles: DemoProfileSummary[];
  onSelect: (id: string) => void;
  loadingId?: string | null;
}) {
  if (profiles.length === 0) {
    return (
      <p className="text-sm text-muted-foreground">Loading demo profiles…</p>
    );
  }
  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      {profiles.map((p) => {
        const Icon = ICONS[p.industry] ?? Building2;
        const isLoading = loadingId === p.profile_id;
        return (
          <Card key={p.profile_id} className="flex flex-col">
            <CardHeader>
              <div className="flex items-start justify-between">
                <Icon className="h-6 w-6 text-muted-foreground" />
                <Badge variant="outline" className="capitalize">
                  {p.industry}
                </Badge>
              </div>
              <CardTitle className="mt-2 text-lg">{p.company_name}</CardTitle>
              <CardDescription>
                {p.domain} · {p.employee_count} employees
              </CardDescription>
            </CardHeader>
            <CardContent className="flex-1 flex flex-col justify-between gap-4">
              <p className="text-sm text-muted-foreground leading-relaxed">
                {p.narrative}
              </p>
              <div className="flex items-center justify-between">
                <span className="text-xs text-muted-foreground">
                  Expected posture{" "}
                  <span className={`font-semibold ${scoreColor(p.expected_posture_score)}`}>
                    {p.expected_posture_score}
                  </span>
                  /100
                </span>
                <Button
                  size="sm"
                  onClick={() => onSelect(p.profile_id)}
                  disabled={isLoading}
                >
                  {isLoading ? "Starting…" : "Run assessment"}
                  <ArrowRight className="ml-2 h-4 w-4" />
                </Button>
              </div>
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}
