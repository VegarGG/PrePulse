"use client";

import { useMemo, useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import type { ScanEvent } from "@/lib/types";

export function TraceViewer({ ndjson }: { ndjson: string }) {
  const [filter, setFilter] = useState("");

  const events: ScanEvent[] = useMemo(() => {
    const lines = ndjson.split("\n").filter(Boolean);
    const out: ScanEvent[] = [];
    for (const line of lines) {
      try {
        out.push(JSON.parse(line) as ScanEvent);
      } catch {
        // skip malformed lines
      }
    }
    return out;
  }, [ndjson]);

  const filtered = filter
    ? events.filter(
        (e) =>
          e.type.includes(filter) ||
          JSON.stringify(e.payload).toLowerCase().includes(filter.toLowerCase()),
      )
    : events;

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between gap-4">
          <div>
            <CardTitle>Reasoning trace</CardTitle>
            <CardDescription>
              Every agent lifecycle event, tool call, and tool result for this scan.
            </CardDescription>
          </div>
          <input
            placeholder="filter (type or payload substring)"
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            className="text-xs rounded border bg-background px-2 py-1 w-64"
          />
        </div>
      </CardHeader>
      <CardContent>
        <ScrollArea className="h-[560px] rounded border">
          <ol className="font-mono text-[11px]">
            {filtered.length === 0 && (
              <li className="p-4 text-muted-foreground">No events match.</li>
            )}
            {filtered.map((e, idx) => (
              <li key={idx} className="px-3 py-2 border-b last:border-b-0 hover:bg-muted/40">
                <div className="flex items-baseline gap-3">
                  <span className="text-muted-foreground tabular-nums">
                    {new Date(e.ts * 1000).toISOString().slice(11, 23)}
                  </span>
                  <span className="text-foreground font-semibold">{e.type}</span>
                </div>
                <pre className="mt-1 text-[10px] whitespace-pre-wrap break-all text-muted-foreground">
                  {JSON.stringify(e.payload, null, 2)}
                </pre>
              </li>
            ))}
          </ol>
        </ScrollArea>
      </CardContent>
    </Card>
  );
}
