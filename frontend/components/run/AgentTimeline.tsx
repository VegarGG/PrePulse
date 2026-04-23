"use client";

import { Check, Loader2, X } from "lucide-react";
import { AGENT_COLORS, AGENT_ORDER, type AgentName, type AgentState } from "@/lib/types";

export function AgentTimeline({
  agents,
  pendingAgent,
}: {
  agents: Record<AgentName, AgentState>;
  pendingAgent?: AgentName | null;
}) {
  return (
    <ol className="space-y-3">
      {AGENT_ORDER.map((name) => {
        const s = agents[name];
        const isPending = pendingAgent === name;
        return (
          <li
            key={name}
            className={`rounded-lg border px-4 py-3 transition-colors ${
              s.status === "running" || s.status === "thinking"
                ? "bg-muted/60"
                : s.status === "completed"
                  ? "bg-muted/30"
                  : "bg-background"
            } ${isPending ? "border-rose-400 border-dashed" : ""}`}
          >
            <div className="flex items-center justify-between gap-3">
              <div className="flex items-center gap-3">
                <span
                  className={`h-2 w-2 rounded-full ${AGENT_COLORS[name]} ${
                    s.status === "running" || s.status === "thinking" ? "animate-pulse" : ""
                  }`}
                />
                <span className="font-medium capitalize">{name}</span>
                <span className="text-xs text-muted-foreground">
                  {s.status === "idle" && "waiting"}
                  {s.status === "running" && "starting"}
                  {s.status === "thinking" && "thinking"}
                  {s.status === "completed" && (s.report_summary ?? "done")}
                  {s.status === "errored" && "errored"}
                </span>
              </div>
              <div className="flex items-center gap-2">
                {s.status === "thinking" || s.status === "running" ? (
                  <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
                ) : s.status === "completed" ? (
                  <Check className="h-4 w-4 text-emerald-600" />
                ) : s.status === "errored" ? (
                  <X className="h-4 w-4 text-rose-600" />
                ) : null}
              </div>
            </div>
            {s.tool_calls.length > 0 && (
              <div className="mt-2 flex flex-wrap gap-1">
                {s.tool_calls.map((t) => (
                  <span
                    key={t.call_id}
                    title={`${t.tool}\nargs: ${JSON.stringify(t.args)}${
                      t.duration_ms !== undefined ? `\n${t.duration_ms} ms` : ""
                    }`}
                    className={`text-[10px] rounded border px-1.5 py-0.5 font-mono ${
                      t.ok === false
                        ? "border-rose-400 text-rose-600"
                        : "border-muted text-muted-foreground"
                    }`}
                  >
                    {t.tool}
                  </span>
                ))}
              </div>
            )}
          </li>
        );
      })}
    </ol>
  );
}
