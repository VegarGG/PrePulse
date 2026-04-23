"use client";

import { ScrollArea } from "@/components/ui/scroll-area";
import type { ScanEvent } from "@/lib/types";

const TYPE_COLOR: Record<string, string> = {
  "scan.started": "text-muted-foreground",
  "scan.completed": "text-emerald-600",
  "scan.failed": "text-rose-600",
  "agent.started": "text-blue-600",
  "agent.thinking": "text-muted-foreground",
  "agent.completed": "text-emerald-600",
  "tool.called": "text-violet-600",
  "tool.result": "text-violet-500",
  "action.pending": "text-rose-600",
  "action.approved": "text-emerald-600",
  "action.rejected": "text-muted-foreground",
  "action.executed": "text-teal-600",
  "confidence.flagged": "text-amber-600",
};

function describe(e: ScanEvent): string {
  const p = e.payload as Record<string, unknown>;
  switch (e.type) {
    case "scan.started":
      return `scan started`;
    case "scan.completed":
      return `scan completed`;
    case "scan.failed":
      return `scan failed: ${String(p.error ?? "")}`;
    case "agent.started":
    case "agent.thinking":
    case "agent.completed":
      return `${e.type} · ${String(p.agent ?? "")}`;
    case "tool.called":
      return `→ ${String(p.tool ?? "")}(${Object.keys((p.args as object) ?? {}).join(", ")})`;
    case "tool.result": {
      const duration = p.duration_ms ? `${p.duration_ms}ms` : "";
      return `← ${String(p.tool ?? "")} ${p.ok === false ? "FAILED" : "ok"} ${duration}`;
    }
    case "action.pending":
      return `⚠ action.pending · ${String(p.action ?? "")} [${String(p.severity ?? "")}]`;
    case "action.approved":
      return `✓ approved · ${String(p.action_id ?? "")}`;
    case "action.rejected":
      return `✗ rejected · ${String(p.action_id ?? "")}`;
    case "action.executed":
      return `▶ executed · ${String(p.action_id ?? "")}`;
    case "confidence.flagged":
      return `flag · ${String(p.agent ?? "")}: ${String(p.reason ?? "")}`;
    default:
      return e.type;
  }
}

export function EventFeed({ events }: { events: ScanEvent[] }) {
  return (
    <ScrollArea className="h-[400px] rounded-lg border">
      <ol className="font-mono text-xs">
        {events.length === 0 && (
          <li className="p-4 text-muted-foreground">Waiting for events…</li>
        )}
        {events.map((e, idx) => {
          const ts = new Date(e.ts * 1000).toISOString().slice(11, 19);
          const color = TYPE_COLOR[e.type] ?? "text-foreground";
          return (
            <li
              key={idx}
              className="flex gap-3 px-3 py-1.5 border-b last:border-b-0 hover:bg-muted/40"
            >
              <span className="text-muted-foreground tabular-nums">{ts}</span>
              <span className={`${color} whitespace-pre-wrap`}>{describe(e)}</span>
            </li>
          );
        })}
      </ol>
    </ScrollArea>
  );
}
